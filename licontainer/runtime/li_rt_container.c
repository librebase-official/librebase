/* Trusted OCI container seam — namespaces, cgroups, pivot_root, seccomp.
 * Linked into lic runtime (li_rt) when upstreaming; standalone build via build-runtime-c.sh */

#if defined(__linux__)
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#endif

#include "li_rt_container.h"

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>

#if defined(__linux__)
#include <sched.h>
#include <sys/mount.h>
#include <sys/syscall.h>
#include <unistd.h>
#ifdef HAVE_LIBSECCOMP
#include <seccomp.h>
#endif
#endif

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

static const char* json_skip_ws(const char* p);
static int json_match_key(const char* json, const char* key, const char** value_out);
int container_json_field_str_i(const char* json, const char* key, char* out, size_t cap);

#ifndef LI_CONTAINER_STATE_DIR_DEFAULT
#define LI_CONTAINER_STATE_DIR_DEFAULT "/run/licontainer/containers"
#endif

#ifndef LI_CONTAINER_CGROUP_ROOT_DEFAULT
#define LI_CONTAINER_CGROUP_ROOT_DEFAULT "/sys/fs/cgroup/licontainer"
#endif

static void li_container_copy_str(char* out, size_t cap, const char* src) {
  if (out == NULL || cap == 0) {
    return;
  }
  if (src == NULL) {
    out[0] = '\0';
    return;
  }
  snprintf(out, cap, "%s", src);
}

int container_runtime_tag_i(void) { return 1; }

int container_is_linux_i(void) {
#if defined(__linux__)
  return 1;
#else
  return 0;
#endif
}

void* container_buf_alloc_i(size_t nbytes) {
  if (nbytes == 0) {
    return NULL;
  }
  return malloc(nbytes);
}

void container_buf_free_i(void* p) { free(p); }

int container_path_join_i(const char* a, const char* b, char* out, size_t cap) {
  if (a == NULL || b == NULL || out == NULL || cap == 0) {
    return LI_CONTAINER_ERR;
  }
  snprintf(out, cap, "%s/%s", a, b);
  return LI_CONTAINER_OK;
}

int container_bundle_read_config_i(const char* bundle_path, char* buf, size_t cap) {
  char path[PATH_MAX];
  if (container_path_join_i(bundle_path, "config.json", path, sizeof(path)) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  if (!container_file_exists_i(path)) {
    return LI_CONTAINER_ERR;
  }
  return container_read_file_i(path, buf, cap);
}

int container_bundle_rootfs_exists_i(const char* bundle_path, const char* config_json) {
  char root_rel[256] = "rootfs";
  const char* root_sec = config_json != NULL ? strstr(config_json, "\"root\"") : NULL;
  if (root_sec != NULL) {
    container_json_field_str_i(root_sec, "path", root_rel, sizeof(root_rel));
  }
  char rootfs[PATH_MAX];
  snprintf(rootfs, sizeof(rootfs), "%s/%s", bundle_path, root_rel);
  struct stat st;
  return (stat(rootfs, &st) == 0 && S_ISDIR(st.st_mode)) ? 1 : 0;
}

int container_json_status_i(const char* state_json, char* out, size_t cap) {
  return container_json_field_str_i(state_json, "status", out, cap);
}

int container_json_pid_i(const char* state_json, int32_t* out, int* has_pid) {
  const char* val = NULL;
  if (has_pid != NULL) {
    *has_pid = 0;
  }
  if (out == NULL) {
    return LI_CONTAINER_ERR;
  }
  if (json_match_key(state_json, "pid", &val) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  *out = (int32_t)strtol(val, NULL, 10);
  if (has_pid != NULL) {
    *has_pid = 1;
  }
  return LI_CONTAINER_OK;
}

int container_str_cmp_i(const char* a, const char* b) {
  if (a == NULL && b == NULL) {
    return 0;
  }
  if (a == NULL || b == NULL) {
    return 1;
  }
  return strcmp(a, b);
}

int container_eprint_i(const char* msg) {
  if (msg == NULL) {
    return LI_CONTAINER_ERR;
  }
  fputs(msg, stderr);
  return LI_CONTAINER_OK;
}

int container_getenv_i(const char* name, char* buf, size_t cap) {
  if (name == NULL || buf == NULL || cap == 0) {
    return LI_CONTAINER_ERR;
  }
  const char* v = getenv(name);
  if (v == NULL) {
    buf[0] = '\0';
    return LI_CONTAINER_ERR;
  }
  li_container_copy_str(buf, cap, v);
  return LI_CONTAINER_OK;
}

int container_env_is_i(const char* name, const char* value) {
  char tmp[64];
  if (container_getenv_i(name, tmp, sizeof(tmp)) != LI_CONTAINER_OK) {
    return 0;
  }
  return strcmp(tmp, value) == 0 ? 1 : 0;
}

int container_mkdir_p_i(const char* path) {
  if (path == NULL || path[0] == '\0') {
    return LI_CONTAINER_ERR;
  }
  char buf[PATH_MAX];
  size_t len = strlen(path);
  if (len >= sizeof(buf)) {
    return LI_CONTAINER_ERR;
  }
  memcpy(buf, path, len + 1);
  for (char* p = buf + 1; *p; ++p) {
    if (*p == '/') {
      *p = '\0';
      if (mkdir(buf, 0755) != 0 && errno != EEXIST) {
        return LI_CONTAINER_ERR;
      }
      *p = '/';
    }
  }
  if (mkdir(buf, 0755) != 0 && errno != EEXIST) {
    return LI_CONTAINER_ERR;
  }
  return LI_CONTAINER_OK;
}

int container_file_exists_i(const char* path) {
  if (path == NULL) {
    return 0;
  }
  struct stat st;
  return stat(path, &st) == 0 ? 1 : 0;
}

int container_read_file_i(const char* path, char* buf, size_t cap) {
  if (path == NULL || buf == NULL || cap == 0) {
    return LI_CONTAINER_ERR;
  }
  FILE* f = fopen(path, "rb");
  if (f == NULL) {
    return LI_CONTAINER_ERR;
  }
  size_t n = fread(buf, 1, cap - 1, f);
  buf[n] = '\0';
  fclose(f);
  return (int)n;
}

int container_write_file_i(const char* path, const char* data) {
  if (path == NULL || data == NULL) {
    return LI_CONTAINER_ERR;
  }
  char parent[PATH_MAX];
  li_container_copy_str(parent, sizeof(parent), path);
  char* slash = strrchr(parent, '/');
  if (slash != NULL) {
    *slash = '\0';
    if (parent[0] != '\0') {
      container_mkdir_p_i(parent);
    }
  }
  FILE* f = fopen(path, "wb");
  if (f == NULL) {
    return LI_CONTAINER_ERR;
  }
  size_t len = strlen(data);
  if (fwrite(data, 1, len, f) != len) {
    fclose(f);
    return LI_CONTAINER_ERR;
  }
  fclose(f);
  return LI_CONTAINER_OK;
}

int container_remove_file_i(const char* path) {
  if (path == NULL) {
    return LI_CONTAINER_ERR;
  }
  return unlink(path) == 0 ? LI_CONTAINER_OK : LI_CONTAINER_ERR;
}

int container_remove_dir_i(const char* path) {
  if (path == NULL) {
    return LI_CONTAINER_ERR;
  }
#if defined(__linux__)
  char cmd[PATH_MAX + 32];
  snprintf(cmd, sizeof(cmd), "rm -rf '%s'", path);
  return system(cmd) == 0 ? LI_CONTAINER_OK : LI_CONTAINER_ERR;
#else
  (void)path;
  return LI_CONTAINER_ERR;
#endif
}

static const char* json_skip_ws(const char* p) {
  while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') {
    ++p;
  }
  return p;
}

static int json_match_key(const char* json, const char* key, const char** value_out) {
  if (json == NULL || key == NULL) {
    return LI_CONTAINER_ERR;
  }
  char pattern[128];
  snprintf(pattern, sizeof(pattern), "\"%s\"", key);
  const char* p = json;
  while ((p = strstr(p, pattern)) != NULL) {
    p += strlen(pattern);
    p = json_skip_ws(p);
    if (*p != ':') {
      continue;
    }
    ++p;
    p = json_skip_ws(p);
    *value_out = p;
    return LI_CONTAINER_OK;
  }
  return LI_CONTAINER_ERR;
}

int container_json_field_str_i(const char* json, const char* key, char* out, size_t cap) {
  const char* val = NULL;
  if (json == NULL || out == NULL || cap == 0) {
    return LI_CONTAINER_ERR;
  }
  if (json_match_key(json, key, &val) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  if (*val != '"') {
    return LI_CONTAINER_ERR;
  }
  ++val;
  const char* end = strchr(val, '"');
  if (end == NULL) {
    return LI_CONTAINER_ERR;
  }
  size_t len = (size_t)(end - val);
  if (len >= cap) {
    len = cap - 1;
  }
  memcpy(out, val, len);
  out[len] = '\0';
  return LI_CONTAINER_OK;
}

int container_json_field_int_i(const char* json, const char* key, int32_t* out) {
  const char* val = NULL;
  if (out == NULL) {
    return LI_CONTAINER_ERR;
  }
  if (json_match_key(json, key, &val) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  char* end = NULL;
  long v = strtol(val, &end, 10);
  if (end == val) {
    return LI_CONTAINER_ERR;
  }
  *out = (int32_t)v;
  return LI_CONTAINER_OK;
}

int container_json_field_bool_i(const char* json, const char* key, int* out) {
  const char* val = NULL;
  if (out == NULL) {
    return LI_CONTAINER_ERR;
  }
  if (json_match_key(json, key, &val) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  if (strncmp(val, "true", 4) == 0) {
    *out = 1;
    return LI_CONTAINER_OK;
  }
  if (strncmp(val, "false", 5) == 0) {
    *out = 0;
    return LI_CONTAINER_OK;
  }
  return LI_CONTAINER_ERR;
}

int container_state_dir_i(char* out, size_t cap) {
  char tmp[PATH_MAX];
  if (container_getenv_i("LI_CONTAINER_STATE_DIR", tmp, sizeof(tmp)) != LI_CONTAINER_OK) {
    li_container_copy_str(tmp, sizeof(tmp), LI_CONTAINER_STATE_DIR_DEFAULT);
  }
  li_container_copy_str(out, cap, tmp);
  return LI_CONTAINER_OK;
}

int container_state_path_i(const char* id, char* out, size_t cap) {
  char base[PATH_MAX];
  if (id == NULL || out == NULL) {
    return LI_CONTAINER_ERR;
  }
  container_state_dir_i(base, sizeof(base));
  snprintf(out, cap, "%s/%s.json", base, id);
  return LI_CONTAINER_OK;
}

int container_state_write_i(const char* id, const char* oci_version, const char* status,
                            int32_t pid, int has_pid, const char* bundle, int32_t exit_code,
                            int has_exit) {
  char path[PATH_MAX];
  char json[4096];
  if (container_state_path_i(id, path, sizeof(path)) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  char dir[PATH_MAX];
  li_container_copy_str(dir, sizeof(dir), path);
  char* slash = strrchr(dir, '/');
  if (slash != NULL) {
    *slash = '\0';
    container_mkdir_p_i(dir);
  }
  int n = snprintf(json, sizeof(json),
                   "{\n  \"ociVersion\": \"%s\",\n  \"id\": \"%s\",\n  \"status\": \"%s\"",
                   oci_version != NULL ? oci_version : "1.0.2", id, status);
  if (has_pid) {
    n += snprintf(json + n, sizeof(json) - (size_t)n, ",\n  \"pid\": %d", (int)pid);
  }
  if (bundle != NULL && bundle[0] != '\0') {
    n += snprintf(json + n, sizeof(json) - (size_t)n, ",\n  \"bundle\": \"%s\"", bundle);
  }
  if (has_exit) {
    n += snprintf(json + n, sizeof(json) - (size_t)n, ",\n  \"exitCode\": %d", (int)exit_code);
  }
  snprintf(json + n, sizeof(json) - (size_t)n, "\n}\n");
  return container_write_file_i(path, json);
}

int container_state_read_i(const char* id, char* json_out, size_t cap) {
  char path[PATH_MAX];
  if (container_state_path_i(id, path, sizeof(path)) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  if (!container_file_exists_i(path)) {
    return LI_CONTAINER_ERR;
  }
  return container_read_file_i(path, json_out, cap);
}

int container_state_delete_i(const char* id) {
  char path[PATH_MAX];
  if (container_state_path_i(id, path, sizeof(path)) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  if (!container_file_exists_i(path)) {
    return LI_CONTAINER_OK;
  }
  return container_remove_file_i(path);
}

int container_cgroup_root_i(char* out, size_t cap) {
  char tmp[PATH_MAX];
  if (container_getenv_i("LI_CONTAINER_CGROUP_ROOT", tmp, sizeof(tmp)) != LI_CONTAINER_OK) {
    li_container_copy_str(tmp, sizeof(tmp), LI_CONTAINER_CGROUP_ROOT_DEFAULT);
  }
  li_container_copy_str(out, cap, tmp);
  return LI_CONTAINER_OK;
}

int container_cgroup_path_i(const char* id, char* out, size_t cap) {
  char base[PATH_MAX];
  container_cgroup_root_i(base, sizeof(base));
  snprintf(out, cap, "%s/%s", base, id);
  return LI_CONTAINER_OK;
}

int container_cgroup_create_i(const char* id) {
#if !defined(__linux__)
  (void)id;
  return LI_CONTAINER_ERR;
#else
  char path[PATH_MAX];
  if (container_cgroup_path_i(id, path, sizeof(path)) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  return container_mkdir_p_i(path);
#endif
}

int container_cgroup_remove_i(const char* id) {
  char path[PATH_MAX];
  if (container_cgroup_path_i(id, path, sizeof(path)) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  return container_remove_dir_i(path);
}

int container_cgroup_join_i(const char* id) {
#if !defined(__linux__)
  (void)id;
  return LI_CONTAINER_ERR;
#else
  char path[PATH_MAX];
  char procs[PATH_MAX + 32];
  if (container_cgroup_path_i(id, path, sizeof(path)) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }
  container_mkdir_p_i(path);
  snprintf(procs, sizeof(procs), "%s/cgroup.procs", path);
  char pidbuf[32];
  snprintf(pidbuf, sizeof(pidbuf), "%d", (int)getpid());
  return container_write_file_i(procs, pidbuf);
#endif
}

int container_cgroup_apply_limits_i(const char* cgroup_path, const char* config_json) {
#if !defined(__linux__)
  (void)cgroup_path;
  (void)config_json;
  return LI_CONTAINER_ERR;
#else
  if (cgroup_path == NULL || config_json == NULL) {
    return LI_CONTAINER_ERR;
  }
  char limits_path[PATH_MAX];
  int32_t pids_limit = 256;
  int32_t mem_limit = 0;
  int has_mem = 0;
  const char* resources = strstr(config_json, "\"resources\"");
  if (resources != NULL) {
    const char* pids = strstr(resources, "\"pids\"");
    if (pids != NULL) {
      const char* lim = strstr(pids, "\"limit\"");
      if (lim != NULL) {
        const char* val = lim + strlen("\"limit\"");
        val = json_skip_ws(val);
        if (*val == ':') {
          ++val;
          val = json_skip_ws(val);
          pids_limit = (int32_t)strtol(val, NULL, 10);
        }
      }
    }
    const char* memory = strstr(resources, "\"memory\"");
    if (memory != NULL) {
      const char* val = NULL;
      if (json_match_key(memory, "limit", &val) == LI_CONTAINER_OK) {
        mem_limit = (int32_t)strtol(val, NULL, 10);
        has_mem = 1;
      }
    }
    const char* cpu = strstr(resources, "\"cpu\"");
    if (cpu != NULL) {
      int32_t quota = 0;
      int32_t period = 0;
      const char* val = NULL;
      if (json_match_key(cpu, "quota", &val) == LI_CONTAINER_OK) {
        quota = (int32_t)strtol(val, NULL, 10);
      }
      if (json_match_key(cpu, "period", &val) == LI_CONTAINER_OK) {
        period = (int32_t)strtol(val, NULL, 10);
      }
      if (quota != 0 && period != 0) {
        snprintf(limits_path, sizeof(limits_path), "%s/cpu.max", cgroup_path);
        char cpu_buf[64];
        snprintf(cpu_buf, sizeof(cpu_buf), "%d %d", (int)quota, (int)period);
        container_write_file_i(limits_path, cpu_buf);
      }
    }
  }
  snprintf(limits_path, sizeof(limits_path), "%s/pids.max", cgroup_path);
  char pids_buf[32];
  snprintf(pids_buf, sizeof(pids_buf), "%d", (int)pids_limit);
  container_write_file_i(limits_path, pids_buf);
  if (has_mem) {
    snprintf(limits_path, sizeof(limits_path), "%s/memory.max", cgroup_path);
    char mem_buf[32];
    snprintf(mem_buf, sizeof(mem_buf), "%d", (int)mem_limit);
    container_write_file_i(limits_path, mem_buf);
  }
  return LI_CONTAINER_OK;
#endif
}

int container_stdout_i(const char* msg) {
  if (msg == NULL) {
    return LI_CONTAINER_ERR;
  }
  fputs(msg, stdout);
  return LI_CONTAINER_OK;
}

int container_json_process_uid_i(const char* config_json) {
  const char* process = config_json != NULL ? strstr(config_json, "\"process\"") : NULL;
  if (process == NULL) {
    return 0;
  }
  const char* user = strstr(process, "\"user\"");
  if (user == NULL) {
    return 0;
  }
  const char* val = NULL;
  if (json_match_key(user, "uid", &val) == LI_CONTAINER_OK) {
    return (int)strtol(val, NULL, 10);
  }
  return 0;
}

int container_json_process_gid_i(const char* config_json) {
  const char* process = config_json != NULL ? strstr(config_json, "\"process\"") : NULL;
  if (process == NULL) {
    return 0;
  }
  const char* user = strstr(process, "\"user\"");
  if (user == NULL) {
    return 0;
  }
  const char* val = NULL;
  if (json_match_key(user, "gid", &val) == LI_CONTAINER_OK) {
    return (int)strtol(val, NULL, 10);
  }
  return 0;
}

int container_state_pid_value_i(const char* state_json) {
  int32_t pid = -1;
  int has = 0;
  if (container_json_pid_i(state_json, &pid, &has) == LI_CONTAINER_OK && has) {
    return (int)pid;
  }
  return -1;
}

int container_namespace_flags_i(const char* config_json) {
#if !defined(__linux__)
  (void)config_json;
  return 0;
#else
  uint64_t flags = 0;
  const char* linux_sec = config_json != NULL ? strstr(config_json, "\"linux\"") : NULL;
  const char* ns = linux_sec != NULL ? strstr(linux_sec, "\"namespaces\"") : NULL;
  if (ns == NULL) {
    return (int)(CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC);
  }
  const char* p = ns;
  while ((p = strstr(p, "\"type\"")) != NULL) {
    p += strlen("\"type\"");
    p = json_skip_ws(p);
    if (*p != ':') {
      continue;
    }
    ++p;
    p = json_skip_ws(p);
    if (*p != '"') {
      continue;
    }
    ++p;
    if (strncmp(p, "pid", 3) == 0) {
      flags |= CLONE_NEWPID;
    } else if (strncmp(p, "net", 3) == 0) {
      flags |= CLONE_NEWNET;
    } else if (strncmp(p, "mnt", 3) == 0) {
      flags |= CLONE_NEWNS;
    } else if (strncmp(p, "uts", 3) == 0) {
      flags |= CLONE_NEWUTS;
    } else if (strncmp(p, "ipc", 3) == 0) {
      flags |= CLONE_NEWIPC;
    } else if (strncmp(p, "user", 4) == 0) {
      flags |= CLONE_NEWUSER;
    }
    ++p;
  }
  if (flags == 0) {
    flags = CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC;
  }
  return (int)flags;
#endif
}

int container_unshare_i(uint64_t flags) {
#if !defined(__linux__)
  (void)flags;
  return LI_CONTAINER_ERR;
#else
  if (unshare((int)flags) != 0) {
    return LI_CONTAINER_ERR;
  }
  return LI_CONTAINER_OK;
#endif
}

int container_fork_child_i(void) {
#if !defined(__linux__)
  return LI_CONTAINER_ERR;
#else
  pid_t pid = fork();
  if (pid < 0) {
    return LI_CONTAINER_ERR;
  }
  return (int)pid;
#endif
}

int container_pivot_root_i(const char* rootfs_path) {
#if !defined(__linux__)
  (void)rootfs_path;
  return LI_CONTAINER_ERR;
#else
  char old_root[PATH_MAX];
  snprintf(old_root, sizeof(old_root), "%s/.old_root", rootfs_path);
  container_mkdir_p_i(old_root);
  if (chdir(rootfs_path) != 0) {
    return LI_CONTAINER_ERR;
  }
  if (syscall(SYS_pivot_root, ".", ".old_root") != 0) {
    return LI_CONTAINER_ERR;
  }
  if (chdir("/") != 0) {
    return LI_CONTAINER_ERR;
  }
  umount2("/.old_root", MNT_DETACH);
  rmdir("/.old_root");
  return LI_CONTAINER_OK;
#endif
}

static int setup_mount(const char* rootfs, const char* dest_rel, const char* mtype,
                       const char* source, const char* data) {
#if !defined(__linux__)
  (void)rootfs;
  (void)dest_rel;
  (void)mtype;
  (void)source;
  (void)data;
  return LI_CONTAINER_ERR;
#else
  char dest[PATH_MAX];
  snprintf(dest, sizeof(dest), "%s/%s", rootfs, dest_rel);
  container_mkdir_p_i(dest);
  unsigned long flags = 0;
  const char* fstype = mtype;
  const char* src = source;
  if (strcmp(mtype, "bind") == 0) {
    fstype = NULL;
    flags = MS_BIND | MS_REC;
    if (!container_file_exists_i(source)) {
      return LI_CONTAINER_OK;
    }
  }
  if (mount(src, dest, fstype, flags, data) != 0) {
    return LI_CONTAINER_ERR;
  }
  return LI_CONTAINER_OK;
#endif
}

int container_setup_rootfs_i(const char* bundle_path, const char* config_json) {
#if !defined(__linux__)
  (void)bundle_path;
  (void)config_json;
  return LI_CONTAINER_ERR;
#else
  char root_rel[256];
  if (container_json_field_str_i(config_json, "path", root_rel, sizeof(root_rel)) != LI_CONTAINER_OK) {
    const char* root_sec = strstr(config_json, "\"root\"");
    if (root_sec != NULL) {
      container_json_field_str_i(root_sec, "path", root_rel, sizeof(root_rel));
    }
  }
  char rootfs[PATH_MAX];
  snprintf(rootfs, sizeof(rootfs), "%s/%s", bundle_path, root_rel);

  const char* mounts = strstr(config_json, "\"mounts\"");
  if (mounts != NULL) {
    const char* p = mounts;
    while ((p = strstr(p, "\"destination\"")) != NULL) {
      char dest[256] = {0};
      char mtype[64] = {0};
      char source[256] = {0};
      const char* val = NULL;
      if (json_match_key(p, "destination", &val) == LI_CONTAINER_OK && *val == '"') {
        ++val;
        const char* end = strchr(val, '"');
        if (end) {
          size_t n = (size_t)(end - val);
          if (n >= sizeof(dest)) {
            n = sizeof(dest) - 1;
          }
          memcpy(dest, val, n);
        }
      }
      const char* block = p;
      if (json_match_key(block, "type", &val) == LI_CONTAINER_OK && *val == '"') {
        ++val;
        const char* end = strchr(val, '"');
        if (end) {
          size_t n = (size_t)(end - val);
          if (n >= sizeof(mtype)) {
            n = sizeof(mtype) - 1;
          }
          memcpy(mtype, val, n);
        }
      }
      if (json_match_key(block, "source", &val) == LI_CONTAINER_OK && *val == '"') {
        ++val;
        const char* end = strchr(val, '"');
        if (end) {
          size_t n = (size_t)(end - val);
          if (n >= sizeof(source)) {
            n = sizeof(source) - 1;
          }
          memcpy(source, val, n);
        }
      }
      char dest_trim[256];
      const char* d = dest;
      while (*d == '/') {
        ++d;
      }
      li_container_copy_str(dest_trim, sizeof(dest_trim), d);
      if (strcmp(mtype, "proc") == 0) {
        setup_mount(rootfs, dest_trim, "proc", "proc", NULL);
      } else if (strcmp(mtype, "tmpfs") == 0) {
        setup_mount(rootfs, dest_trim, "tmpfs", source[0] ? source : "tmpfs", "mode=1777");
      } else if (strcmp(mtype, "bind") == 0) {
        setup_mount(rootfs, dest_trim, "bind", source, NULL);
      }
      ++p;
    }
  }

  setup_mount(rootfs, "tmp", "tmpfs", "tmpfs", "mode=1777");
  setup_mount(rootfs, "run", "tmpfs", "tmpfs", "mode=1777");

  if (container_pivot_root_i(rootfs) != LI_CONTAINER_OK) {
    return LI_CONTAINER_ERR;
  }

  int ro = 0;
  const char* root_sec = strstr(config_json, "\"root\"");
  if (root_sec != NULL) {
    container_json_field_bool_i(root_sec, "readonly", &ro);
  }
  if (ro) {
    mount(NULL, "/", NULL, MS_RDONLY | MS_REMOUNT, NULL);
  }

  char hostname[256];
  if (container_json_field_str_i(config_json, "hostname", hostname, sizeof(hostname)) == LI_CONTAINER_OK) {
    container_write_file_i("/etc/hostname", hostname);
    sethostname(hostname, strlen(hostname));
  }
  return LI_CONTAINER_OK;
#endif
}

int container_drop_privileges_i(uint32_t uid, uint32_t gid) {
#if !defined(__linux__)
  (void)uid;
  (void)gid;
  return LI_CONTAINER_ERR;
#else
  if (setgid((gid_t)gid) != 0) {
    return LI_CONTAINER_ERR;
  }
  if (setuid((uid_t)uid) != 0) {
    return LI_CONTAINER_ERR;
  }
  return LI_CONTAINER_OK;
#endif
}

int container_exec_i(const char* cwd, const char* config_json) {
#if !defined(__linux__)
  (void)cwd;
  (void)config_json;
  return LI_CONTAINER_ERR;
#else
  const char* process = strstr(config_json, "\"process\"");
  if (process == NULL) {
    return LI_CONTAINER_ERR;
  }
  if (cwd != NULL && chdir(cwd) != 0) {
    return LI_CONTAINER_ERR;
  }
  const char* args_key = strstr(process, "\"args\"");
  if (args_key == NULL) {
    return LI_CONTAINER_ERR;
  }
  const char* arr = strchr(args_key, '[');
  if (arr == NULL) {
    return LI_CONTAINER_ERR;
  }
  char* argv[64];
  int argc = 0;
  const char* p = arr + 1;
  while (*p && argc < 63) {
    p = json_skip_ws(p);
    if (*p == ']') {
      break;
    }
    if (*p != '"') {
      break;
    }
    ++p;
    const char* end = strchr(p, '"');
    if (end == NULL) {
      break;
    }
    size_t len = (size_t)(end - p);
    char* arg = malloc(len + 1);
    if (arg == NULL) {
      return LI_CONTAINER_ERR;
    }
    memcpy(arg, p, len);
    arg[len] = '\0';
    argv[argc++] = arg;
    p = end + 1;
    p = json_skip_ws(p);
    if (*p == ',') {
      ++p;
    }
  }
  argv[argc] = NULL;
  if (argc == 0) {
    return LI_CONTAINER_ERR;
  }
  char** envp = NULL;
  const char* env_key = strstr(process, "\"env\"");
  if (env_key != NULL) {
    const char* earr = strchr(env_key, '[');
    if (earr != NULL) {
      char* envv[128];
      int envc = 0;
      p = earr + 1;
      while (*p && envc < 127) {
        p = json_skip_ws(p);
        if (*p == ']') {
          break;
        }
        if (*p != '"') {
          break;
        }
        ++p;
        const char* end = strchr(p, '"');
        if (end == NULL) {
          break;
        }
        size_t len = (size_t)(end - p);
        char* e = malloc(len + 1);
        if (e == NULL) {
          break;
        }
        memcpy(e, p, len);
        e[len] = '\0';
        envv[envc++] = e;
        p = end + 1;
        p = json_skip_ws(p);
        if (*p == ',') {
          ++p;
        }
      }
      envv[envc] = NULL;
      if (envc > 0) {
        envp = calloc((size_t)envc + 1, sizeof(char*));
        for (int i = 0; i < envc; ++i) {
          envp[i] = envv[i];
        }
      }
    }
  }
  execve(argv[0], argv, envp);
  return LI_CONTAINER_ERR;
#endif
}

int container_kill_i(int32_t pid, int32_t signal) {
#if !defined(__linux__)
  (void)pid;
  (void)signal;
  return LI_CONTAINER_ERR;
#else
  if (pid <= 0) {
    return LI_CONTAINER_OK;
  }
  if (kill((pid_t)pid, (int)signal) != 0) {
    return LI_CONTAINER_ERR;
  }
  return LI_CONTAINER_OK;
#endif
}

int container_pid_alive_i(int32_t pid) {
#if !defined(__linux__)
  (void)pid;
  return 0;
#else
  if (pid <= 0) {
    return 0;
  }
  return kill((pid_t)pid, 0) == 0 ? 1 : 0;
#endif
}

static const char* default_seccomp_syscalls[] = {
    "read",       "write",      "open",        "close",       "stat",        "fstat",
    "exit",       "exit_group", "clone",       "fork",        "execve",      "wait4",
    "getpid",     "gettid",     "mmap",        "munmap",      "brk",         "fcntl",
    "openat",     "newfstatat", "getcwd",      "chdir",       "mkdir",       "rmdir",
    "unlink",     "getuid",     "getgid",      "setuid",      "setgid",      "prctl",
    "arch_prctl", "futex",      "rt_sigaction"};

int container_seccomp_apply_i(const char* config_json) {
#if !defined(__linux__)
  (void)config_json;
  return LI_CONTAINER_OK;
#else
  if (container_env_is_i("LI_CONTAINER_SKIP_SECCOMP", "1")) {
    return LI_CONTAINER_OK;
  }
#ifdef HAVE_LIBSECCOMP
  scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ERRNO(1));
  if (ctx == NULL) {
    goto fail;
  }
  seccomp_arch_add(ctx, SCMP_ARCH_NATIVE);
  const char* linux_sec = config_json != NULL ? strstr(config_json, "\"linux\"") : NULL;
  const char* seccomp_sec = linux_sec != NULL ? strstr(linux_sec, "\"seccomp\"") : NULL;
  if (seccomp_sec != NULL) {
    const char* p = seccomp_sec;
    while ((p = strstr(p, "\"names\"")) != NULL) {
      const char* arr = strchr(p, '[');
      if (arr == NULL) {
        break;
      }
      const char* q = arr + 1;
      while (*q) {
        q = json_skip_ws(q);
        if (*q == ']') {
          break;
        }
        if (*q != '"') {
          break;
        }
        ++q;
        const char* end = strchr(q, '"');
        if (end == NULL) {
          break;
        }
        char name[64];
        size_t n = (size_t)(end - q);
        if (n >= sizeof(name)) {
          n = sizeof(name) - 1;
        }
        memcpy(name, q, n);
        name[n] = '\0';
        int nr = seccomp_syscall_resolve_name(name);
        if (nr >= 0) {
          seccomp_rule_add(ctx, SCMP_ACT_ALLOW, nr, 0);
        }
        q = end + 1;
        q = json_skip_ws(q);
        if (*q == ',') {
          ++q;
        }
      }
      break;
    }
  } else {
    for (size_t i = 0; i < sizeof(default_seccomp_syscalls) / sizeof(default_seccomp_syscalls[0]); ++i) {
      int nr = seccomp_syscall_resolve_name(default_seccomp_syscalls[i]);
      if (nr >= 0) {
        seccomp_rule_add(ctx, SCMP_ACT_ALLOW, nr, 0);
      }
    }
  }
  if (seccomp_load(ctx) != 0) {
    seccomp_release(ctx);
    goto fail;
  }
  seccomp_release(ctx);
  return LI_CONTAINER_OK;
fail:
  if (container_env_is_i("LI_CONTAINER_STRICT_SECCOMP", "1")) {
    return LI_CONTAINER_ERR;
  }
  container_eprint_i("lirun: seccomp skipped: libseccomp load failed\n");
  return LI_CONTAINER_OK;
#else
  if (container_env_is_i("LI_CONTAINER_STRICT_SECCOMP", "1")) {
    container_eprint_i("lirun: seccomp: no libseccomp at build time\n");
    return LI_CONTAINER_ERR;
  }
  container_eprint_i("lirun: seccomp skipped: built without libseccomp\n");
  return LI_CONTAINER_OK;
#endif
#endif
}

#ifndef LI_RT_CONTAINER_H
#define LI_RT_CONTAINER_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define LI_CONTAINER_OK 0
#define LI_CONTAINER_ERR (-1)

int container_runtime_tag_i(void);
int container_is_linux_i(void);

int container_mkdir_p_i(const char* path);
int container_file_exists_i(const char* path);
int container_read_file_i(const char* path, char* buf, size_t cap);
int container_write_file_i(const char* path, const char* data);
int container_remove_file_i(const char* path);
int container_remove_dir_i(const char* path);
int container_getenv_i(const char* name, char* buf, size_t cap);
int container_env_is_i(const char* name, const char* value);

int container_json_field_str_i(const char* json, const char* key, char* out, size_t cap);
int container_json_field_int_i(const char* json, const char* key, int32_t* out);
int container_json_field_bool_i(const char* json, const char* key, int* out);

int container_state_dir_i(char* out, size_t cap);
int container_state_path_i(const char* id, char* out, size_t cap);
int container_state_write_i(const char* id, const char* oci_version, const char* status,
                            int32_t pid, int has_pid, const char* bundle, int32_t exit_code,
                            int has_exit);
int container_state_read_i(const char* id, char* json_out, size_t cap);
int container_state_delete_i(const char* id);

int container_cgroup_root_i(char* out, size_t cap);
int container_cgroup_path_i(const char* id, char* out, size_t cap);
int container_cgroup_create_i(const char* id);
int container_cgroup_remove_i(const char* id);
int container_cgroup_join_i(const char* id);
int container_cgroup_apply_limits_i(const char* cgroup_path, const char* config_json);

int container_namespace_flags_i(const char* config_json);
int container_json_process_uid_i(const char* config_json);
int container_json_process_gid_i(const char* config_json);
int container_state_pid_value_i(const char* state_json);
int container_stdout_i(const char* msg);
int container_unshare_i(uint64_t flags);

int container_fork_child_i(void);
int container_pivot_root_i(const char* rootfs_path);
int container_setup_rootfs_i(const char* bundle_path, const char* config_json);
int container_drop_privileges_i(uint32_t uid, uint32_t gid);
int container_exec_i(const char* cwd, const char* config_json);
int container_kill_i(int32_t pid, int32_t signal);
int container_pid_alive_i(int32_t pid);

int container_seccomp_apply_i(const char* config_json);
int container_eprint_i(const char* msg);
void* container_buf_alloc_i(size_t nbytes);
void container_buf_free_i(void* p);
int container_str_cmp_i(const char* a, const char* b);
int container_path_join_i(const char* a, const char* b, char* out, size_t cap);
int container_bundle_read_config_i(const char* bundle_path, char* buf, size_t cap);
int container_bundle_rootfs_exists_i(const char* bundle_path, const char* config_json);
int container_json_status_i(const char* state_json, char* out, size_t cap);
int container_json_pid_i(const char* state_json, int32_t* out, int* has_pid);

#ifdef __cplusplus
}
#endif

#endif /* LI_RT_CONTAINER_H */

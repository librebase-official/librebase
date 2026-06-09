# li_rt_container — trusted OCI runtime seam for licontainer.
# Link into lic `li_rt` when upstreaming:
#   list(APPEND LI_RT_SOURCES .../li_rt_container.c)
#   target_link_libraries(li_rt PRIVATE ${SECCOMP_LIBRARIES})

add_library(li_rt_container STATIC
  li_rt_container.c
)

target_include_directories(li_rt_container PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

option(LI_CONTAINER_USE_LIBSECCOMP "Link libseccomp for seccomp profiles" ON)

if(LI_CONTAINER_USE_LIBSECCOMP)
  find_package(PkgConfig QUIET)
  if(PkgConfig_FOUND)
    pkg_check_modules(SECCOMP libseccomp)
  endif()
  if(SECCOMP_FOUND)
    target_compile_definitions(li_rt_container PRIVATE HAVE_LIBSECCOMP)
    target_include_directories(li_rt_container PRIVATE ${SECCOMP_INCLUDE_DIRS})
    target_link_libraries(li_rt_container PRIVATE ${SECCOMP_LIBRARIES})
  endif()
endif()

install(FILES li_rt_container.h seam-container.li DESTINATION share/licontainer/runtime)

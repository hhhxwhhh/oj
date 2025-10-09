cmake_minimum_required(VERSION 3.5)
project(judger C)

#set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

if(APPLE)
    set(CMAKE_C_FLAGS "-g -Wall -Werror -O3 -std=c99 -fPIC")
else()
    set(CMAKE_C_FLAGS "-g -Wall -Werror -O3 -std=c99 -pie -fPIC")
endif()

# make judger lib
file(GLOB SOURCE "src/*.c" "src/rules/*.c")
add_library(libjudger SHARED ${SOURCE})
set_target_properties(libjudger PROPERTIES PREFIX "")
target_link_libraries(libjudger pthread seccomp)


install(FILES ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/libjudger.so
    PERMISSIONS OWNER_EXECUTE OWNER_READ
    DESTINATION /usr/lib/judger)
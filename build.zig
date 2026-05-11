const std = @import("std");
pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});
    const mod = b.createModule(.{
        .root_source_file = b.path("zig-src/lib.zig"),
        .target = target,
        .optimize = optimize,
    });
    const lib = b.addLibrary(.{
        .name = "module",
        .linkage = .dynamic,
        .root_module = mod,
    });

    // Install to the python module directory with specific file name
    b.lib_dir = "./src/blindrsa/";
    const copy_file = b.addInstallLibFile(lib.getEmittedBin(), "_lib.so");
    b.getInstallStep().dependOn(&copy_file.step);

    const blind = b.dependency("blind_rsa_signatures", .{
        .target = target,
        .optimize = optimize,
    });
    lib.root_module.addImport("blind_rsa_signatures", blind.module("blind_rsa_signatures"));
}

const std = @import("std");
const blindrsa = @import("blind_rsa_signatures").brsa.BlindRsaPSSDeterministic(2048);

var gpa = std.heap.c_allocator;

const SecretKey = blindrsa.SecretKey;
const PublicKey = blindrsa.PublicKey;
const ErrorName = [*:0]const u8;

// Generate keypair

pub export fn generate_keypair(sk: *[2048]u8, sk_len: *usize, pk: *[2048]u8, pk_len: *usize) ?ErrorName {
    // ~1192 bytes required
    const kp = blindrsa.KeyPair.generate() catch |err| return @errorName(err);
    defer kp.deinit();
    const sk_der = kp.sk.serialize(sk) catch |err| return @errorName(err);
    sk_len.* = sk_der.len;
    const pk_der = kp.pk.serialize(pk) catch |err| return @errorName(err);
    pk_len.* = pk_der.len;
    return null;
}

// SecretKey

pub export fn sk_init(sk_bytes: [*]u8, sk_len: usize) ?*SecretKey {
    const sk: *SecretKey = gpa.create(SecretKey) catch return null;
    sk.* = SecretKey.import(sk_bytes[0..sk_len]) catch return null;
    return sk;
}

pub export fn sk_deinit(sk: *SecretKey) void {
    sk.deinit();
    gpa.destroy(sk);
}

pub export fn sk_sign(sk: *SecretKey, msg: *const [256]u8, signed: *[256]u8) ?ErrorName {
    signed.* = sk.blindSign(msg.*) catch |err| return @errorName(err);
    return null;
}

// PublicKey

pub export fn pk_init(pk_bytes: [*]u8, pk_len: usize) ?*PublicKey {
    const pk: *PublicKey = gpa.create(PublicKey) catch return null;
    pk.* = PublicKey.import(pk_bytes[0..pk_len]) catch return null;
    return pk;
}

pub export fn pk_deinit(pk: *PublicKey) void {
    pk.deinit();
    gpa.destroy(pk);
}

pub export fn pk_blind(
    pk: *PublicKey,
    msg: [*]const u8,
    msg_len: usize,
    blinded: *[256]u8,
    secret: *[256]u8,
    // msg_randomizer: *[32]u8,
) ?ErrorName {
    const blinding_result = pk.blind(msg[0..msg_len]) catch |err| return @errorName(err);
    blinded.* = blinding_result.blind_message;
    secret.* = blinding_result.secret;
    // msg_randomizer.* = blinding_result.msg_randomizer;
    return null;
}

pub export fn pk_finalize(
    pk: *PublicKey,
    signed: *[256]u8,
    blinded: *[256]u8,
    secret: *[256]u8,
    // msg_randomizer: *[32]u8,
    msg: [*]u8,
    msg_len: usize,
    signature: *[256]u8,
) ?ErrorName {
    signature.* = pk.finalize(
        signed.*,
        &blindrsa.BlindingResult{
            .blind_message = blinded.*,
            .secret = secret.*,
            .msg_randomizer = null, //msg_randomizer.*,
        },
        msg[0..msg_len],
    ) catch |err| return @errorName(err);
    return null;
}

pub export fn pk_verify(
    pk: *PublicKey,
    signature: *[256]u8,
    // msg_randomizer: *[32]u8,
    msg: [*]u8,
    msg_len: usize,
) ?ErrorName {
    pk.verify(
        signature.*,
        null, // msg_randomizer.*,
        msg[0..msg_len],
    ) catch |err| return @errorName(err);
    return null;
}

export const exports: [*:0]const u8 = blk: {
    var str: []const u8 = "";
    for (@typeInfo(@This()).@"struct".decls) |decl| {
        const function_name = decl.name;
        const field = @field(@This(), decl.name);
        if (@typeInfo(@TypeOf(field)) != .@"fn") continue;
        const fn_info = @typeInfo(@TypeOf(field)).@"fn";
        const return_type_name = @typeName(fn_info.return_type.?);
        str = str ++ function_name ++ "(";
        for (fn_info.params, 0..) |p, i| {
            if (i != 0) {
                str = str ++ ", ";
            }
            const param_type_name = @typeName(p.type.?);
            str = str ++ param_type_name;
        }
        str = str ++ ") " ++ return_type_name ++ "\n";
    }
    break :blk str ++ "\x00";
};

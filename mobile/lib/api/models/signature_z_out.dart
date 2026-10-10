// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'z_user_out.dart';

part 'signature_z_out.g.dart';

/// Who can use a signature Z-Move: holding ``crystal``, ``base_move`` becomes it.
@JsonSerializable()
class SignatureZOut {
  const SignatureZOut({
    required this.baseMove,
    required this.crystal,
    required this.users,
  });
  
  factory SignatureZOut.fromJson(Map<String, Object?> json) => _$SignatureZOutFromJson(json);
  
  @JsonKey(name: 'base_move')
  final String baseMove;
  final String crystal;
  final List<ZUserOut> users;

  Map<String, Object?> toJson() => _$SignatureZOutToJson(this);
}

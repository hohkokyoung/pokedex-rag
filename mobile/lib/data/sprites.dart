/// Artwork URLs on the pokérag server. Mirrors the website's `thumb()`: list rows use
/// the small WebP copy (96 px, 2× for ≤ 48 pt; else 320 px). The server falls back to
/// the full PNG when a thumb hasn't been built, so these are always safe.
String spriteUrl(String base, String? path) {
  if (path == null || path.isEmpty) return '';
  if (path.startsWith('http')) return path;
  return '$base${path.startsWith('/') ? '' : '/'}$path';
}

String thumbUrl(String base, String? path, {double pt = 48}) {
  final url = spriteUrl(base, path);
  final size = pt <= 48 ? 96 : 320;
  return url.replaceFirstMapped(
    RegExp(r'/sprites/(?!thumbs/)(.+)\.png(\?.*)?$'),
    (m) => '/sprites/thumbs/$size/${m[1]}.webp',
  );
}

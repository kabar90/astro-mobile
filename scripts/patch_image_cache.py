from pathlib import Path

target = Path("astro_mobile/lib/widgets/astro_cached_image.dart")
if not target.is_file():
    raise SystemExit(f"Image widget not found: {target}")

source = r'''import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_cache_manager/flutter_cache_manager.dart';

/// One network request per cache miss, with persistent disk and memory caching.
/// CachedNetworkImage performs the download and cache write together; it does
/// not start a second parallel request just to warm a separate cache.
class AstroCachedImage extends StatelessWidget {
  const AstroCachedImage({
    super.key,
    required this.imageUrl,
    this.fit = BoxFit.contain,
    this.placeholder,
    this.errorWidget,
  });

  final String imageUrl;
  final BoxFit fit;
  final Widget? placeholder;
  final Widget? errorWidget;

  static final CacheManager _cacheManager = CacheManager(
    Config(
      'astro_mobile_product_images_v2',
      stalePeriod: const Duration(days: 90),
      maxNrOfCacheObjects: 500,
    ),
  );

  bool _isValidUrl(String value) {
    final uri = Uri.tryParse(value);
    return uri != null &&
        (uri.scheme == 'https' || uri.scheme == 'http') &&
        uri.host.isNotEmpty;
  }

  Widget _placeholder() => placeholder ?? const Center(
        child: SizedBox(
          width: 22,
          height: 22,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      );

  Widget _error() => errorWidget ?? const Icon(
        Icons.image_not_supported_outlined,
        color: Colors.black26,
      );

  @override
  Widget build(BuildContext context) {
    final url = imageUrl.trim();
    if (!_isValidUrl(url)) return _error();

    return CachedNetworkImage(
      imageUrl: url,
      cacheKey: url,
      cacheManager: _cacheManager,
      fit: fit,
      width: double.infinity,
      height: double.infinity,
      memCacheWidth: 1200,
      maxWidthDiskCache: 1600,
      fadeInDuration: Duration.zero,
      placeholder: (context, url) => _placeholder(),
      errorWidget: (context, url, error) => _error(),
    );
  }
}
'''

target.write_text(source, encoding="utf-8")
print(f"Patched {target}: single-request persistent image cache enabled.")

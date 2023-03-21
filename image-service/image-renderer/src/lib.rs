pub mod cube_level;
mod imageops;


/// Struct that holds all other renders provided by the image_renderer.
/// Should be used in favour of creating the other renderers individually 
/// 
/// Any multithreading/... should be handled by the creator of the ImageRenderer
pub struct ImageRenderer<'a> {
    pub cube_level_renderer: cube_level::CubeLevelRenderer<'a>,
}

impl ImageRenderer<'_> {

    /// Create a new ImageRenderer. Can be used as a wrapper over all provided renderers.
    pub fn new() -> ImageRenderer<'static> {
        ImageRenderer {
            cube_level_renderer: cube_level::CubeLevelRenderer::new()
        }
    }
}
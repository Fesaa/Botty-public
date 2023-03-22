use image::{RgbaImage, Rgba, DynamicImage, ImageBuffer, ImageFormat};
use image::imageops::{overlay, resize, FilterType, vertical_gradient};
use imageproc::drawing::{draw_text_mut};
use rusttype::{Font, Scale};

use crate::imageops::rounded_corners;

type Image = ImageBuffer<Rgba<u8>, Vec<u8>>;

const MAIN_BRAND_COLOUR: Rgba<u8> = Rgba([106, 86, 246, 255]);
const SECONDARY_BRAND_COLOUR: Rgba<u8> = Rgba([93, 206, 205, 255]);

pub struct CubeLevelRenderer<'a> {
    _cube_logo: DynamicImage,
    lvl_underlay: Image,
    font: Font<'a>,
}

impl CubeLevelRenderer<'_> {

    /// Create a CubeLevelRenderer. Creates some heavy assets on creation. Recommended to only share one.
    /// 
    /// Consider using the [ImageRenderer](crate::ImageRenderer) as a smart wrapper.
    /// 
    /// # Examples
    /// ```no_run
    /// let cube_renderer = CubeLevelRenderer::new();
    /// let level_100_img = cube_renderer.level_statistics(100).unwrap();
    /// level_100_img.save("path/to/save/location/level_100_img.png").unwrap();
    pub fn new() -> CubeLevelRenderer<'static> {
        let cube_logo = image::load_from_memory_with_format(include_bytes!("assets/cube-dark.png"), ImageFormat::Png).unwrap();
        CubeLevelRenderer {
            lvl_underlay: create_level_underlay(&cube_logo).unwrap(),
            _cube_logo: cube_logo,
            font: Font::try_from_vec(Vec::from(include_bytes!("assets/VT323-Regular.ttf") as &[u8])).unwrap(),
        }
    }

    /// Create an image containing the needed experience and wins per game for a specific level
    /// 
    /// # Arguments
    /// 
    /// * `level` - The level you want the stats for
    pub fn level_statistics(&self, level: u32) -> Result<Image, String> {
        self.level_statistics_inner(
            &self.font,
            format!("Level {}", level),
            1,
            level,
            0)
    }

    /// Create an image containing the needed experience and wins per game to reach a further level
    /// 
    /// # Arguments
    /// 
    /// * `current_level` - The level you currently are. Must be lower than `level`
    /// * `level` - The level you want to be
    /// * `current_xp` - The experience you've already collected on your current level
    pub fn level_statistics_difference(&self, current_level: u32, level: u32, current_xp: u32) -> Result<Image, String> {
        if current_level > level {
            return Err(format!("Current level has to be lower than level. {current_level} < {level}"));
        }

        self.level_statistics_inner(
            &self.font,
            format!("{} -> {}", current_level, level),
            current_level,
            level,
            current_xp)
    }

    fn level_statistics_inner(
        &self,
        font: &Font,
        title: String,
        level_one: u32,
        level_two: u32,
        current_xp: u32
    ) -> Result<ImageBuffer<Rgba<u8>, Vec<u8>>, String> {
        let mut img = self.lvl_underlay.clone();
    
        let title_scale = Scale {
            x: 160.0,
            y: 80.0,
        };
        let text_scale = Scale {
            x: 60.0,
            y: 40.0
        };
    
        let xp_needed = xp_from_level(level_two) - xp_from_level(level_one) - current_xp;
    
        draw_text_mut(&mut img, Rgba([0, 0, 0, 255]), 20, 30, title_scale, &font, &title);
        apply_xp_requirements(&mut img, font, text_scale, Rgba([0, 0, 0, 255]), xp_needed, 20, 70, 50);
    
        Ok(img)
    }
}

/// Total experience needed to reach a level starting at level one.
pub fn xp_from_level(level: u32) -> u32 {
    900 * (level - 1) + 100 * (level - 1) * (level - 1)
}

fn create_level_underlay(cube_logo: &DynamicImage) -> Result<Image, String> {
    let (width, height) = (960, 540);
    let mut img = RgbaImage::new(width, height);

    let nwidth = 250;
    let nheight = nwidth * 1.14 as u32;
    let cube_logo = resize(cube_logo, nwidth, nheight, FilterType::CatmullRom);

    vertical_gradient(&mut img, &MAIN_BRAND_COLOUR, &SECONDARY_BRAND_COLOUR);
    overlay(&mut img, &cube_logo, (width - nwidth - 10) as i64, 60);
    rounded_corners(&mut img, 10);

    Ok(img)
}

fn apply_xp_requirements(
    img: &mut RgbaImage,
    font: &Font,
    text_scale: Scale,
    text_colour: Rgba<u8>,
    total_xp: u32,
    x_jump: i32,
    y_jump: i32,
    y_increment: i32
) {
    let thanks_from_multies = total_xp / 100 as u32;
    let info_text = vec![
        format!("Total XP: {}", total_xp),
        format!("That's {} EggWars games,", total_xp / 250 as u32),
        format!("Or {} SkyWars games,", total_xp / 125 as u32),
        format!("Or {} Lucky Islands games,", total_xp / 120 as u32),
        format!("Or {} /thanks from multipliers,", thanks_from_multies),
        format!("Which is {}/{} multipliers", thanks_from_multies / 700 as u32 + 1, thanks_from_multies/400 as u32 + 1),
        format!("   at 400/700 thanks a multiplier.")
    ];

    for (index, text) in info_text.iter().enumerate() {
        draw_text_mut(img, text_colour, x_jump, y_jump + (y_increment * ((index + 1) as i32)) as i32, text_scale, &font, &text)
    }
}

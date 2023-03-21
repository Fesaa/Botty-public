use image::{ImageBuffer, Rgba};


pub fn rounded_corners(img: &mut ImageBuffer<Rgba<u8>, Vec<u8>>, size: u32) {
    let (width, height) = img.dimensions();

    let x_size = width * size / 100;
    let y_size = height * size / 100;

    if x_size == 0 || y_size == 0 {
        return;
    }

    for (mut x,mut y, pixel) in img.enumerate_pixels_mut() {
        if x > x_size && x < width - x_size {
            continue;
        }
        if y > y_size && y < height - y_size {
            continue;
        }

        if x > x_size{
           x -= width - 2 * x_size
        }

        if y > y_size{
            y -= height - 2 * y_size;
        }

        let (x, y, x_size, y_size) = (x as f32, y as f32, x_size as f32, y_size as f32);

        if (x - x_size) * (x - x_size) / (x_size * x_size) + (y - y_size) * (y - y_size) / (y_size * y_size) <= 1.0 {
            continue;
        }

        *pixel = Rgba([0, 0, 0, 0]);
    }
}
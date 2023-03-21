use std::io::Cursor;

use actix_web::{get, web::{self}, HttpResponse, Responder, web::Data, http::StatusCode};
use image::{DynamicImage, ImageOutputFormat};

use image_renderer::ImageRenderer;

#[get("/")]
pub async fn hello() -> impl Responder {
    HttpResponse::Ok().body("Ameliah loves you <3")
}

#[get("/image_renderer/cube_level/level&{level}")]
pub async fn get_image_renderer_cube_level_level(img_ren: Data<ImageRenderer<'_>> ,path: web::Path<u32>) -> impl Responder {
    let mut level = path.into_inner();
    if level == 0 {
        level = 1;
    }
    let renderer = img_ren.clone();
    let img = renderer.cube_level_renderer.level_statistics(level).unwrap();
    let mut w = Cursor::new(Vec::new());
    DynamicImage::ImageRgba8(img)
        .write_to(&mut w, ImageOutputFormat::Png)
        .unwrap();
    let vec = w.into_inner();

    HttpResponse::build(StatusCode::OK)
        .content_type("image/png")
        .body(vec)
}
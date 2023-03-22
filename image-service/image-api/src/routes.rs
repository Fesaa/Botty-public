use std::{io::Cursor};

use actix_web::{get, web::{self}, HttpResponse, Responder, web::Data, http::StatusCode};
use image::{DynamicImage, ImageOutputFormat, ImageBuffer, Rgba};
use serde::Deserialize;

use image_renderer::ImageRenderer;

#[get("/")]
pub async fn hello() -> impl Responder {
    HttpResponse::Ok().body("Ameliah loves you <3")
}

#[derive(Deserialize)]
pub struct SingleRequest {
    level: u32
}

#[get("/image-renderer/cube-level/single")]
pub async fn get_image_renderer_cube_level_level(img_ren: Data<ImageRenderer<'_>> , info: web::Query<SingleRequest>) -> impl Responder {
    let mut level = info.level;
    if level == 0 {
        level = 1;
    }
    let renderer = img_ren.clone();
    let result = renderer.cube_level_renderer.level_statistics(level);
    image_return(result)
}

#[derive(Deserialize)]
pub struct MultiRequest {
    level1: u32,
    level2: u32,
    current_xp: u32
}

#[get("/image-renderer/cube-level/multi")]
pub async fn get_image_renderer_cube_level_level_distance(img_ren: Data<ImageRenderer<'_>> , info: web::Query<MultiRequest>) -> impl Responder {
    let renderer = img_ren.clone();
    let result = renderer.cube_level_renderer.level_statistics_difference(info.level1, info.level2, info.current_xp);
    image_return(result)
}

fn image_return(result: Result<ImageBuffer<Rgba<u8>, Vec<u8>>, String>) -> impl Responder {
    match result {
        Ok(img) => {
            HttpResponse::build(StatusCode::OK)
                .content_type("image/png")
                .body(img_to_bytes(img))
        },
        Err(err) => HttpResponse::BadRequest().body(err),
    }
}

fn img_to_bytes(img: ImageBuffer<Rgba<u8>, Vec<u8>>) -> Vec<u8> {
    let mut w = Cursor::new(Vec::new());
    DynamicImage::ImageRgba8(img)
        .write_to(&mut w, ImageOutputFormat::Png)
        .unwrap();
    w.into_inner()
}
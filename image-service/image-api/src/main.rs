use std::sync::Arc;
use toml;

use actix_web::{App,HttpServer, web::Data};
use image_renderer::ImageRenderer;
use serde::Deserialize;

mod routes;

#[derive(Deserialize)]
struct Config {
    address: String,
    port: u16,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {

    let config: Config = toml::from_str(&std::fs::read_to_string("config.toml")?).unwrap();

    HttpServer::new(|| {
        App::new()
            .app_data(Data::from(Arc::new(ImageRenderer::new())))
            .service(routes::hello)
            .service(routes::get_image_renderer_cube_level_level)
            .service(routes::get_image_renderer_cube_level_level_distance)
    })
    .bind((config.address, config.port))?
    .run()
    .await
}
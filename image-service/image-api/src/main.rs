use std::sync::Arc;

use actix_web::{App,HttpServer, web::Data};
use image_renderer::ImageRenderer;

mod routes;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .app_data(Data::from(Arc::new(ImageRenderer::new())))
            .service(routes::hello)
            .service(routes::get_image_renderer_cube_level_level)
            .service(routes::get_image_renderer_cube_level_level_distance)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
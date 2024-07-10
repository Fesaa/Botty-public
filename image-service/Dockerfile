FROM rust:1-slim-buster as builder

WORKDIR /app

COPY . .

RUN cargo build --release

FROM debian:buster-slim

WORKDIR /app

COPY --from=builder /app/target/release/image-api /app

CMD ["./image-api"]


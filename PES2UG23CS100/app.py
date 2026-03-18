import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from minio import Minio

app = Flask(__name__)

# -------------------------------
# Block Storage (Ceph via volume)
# -------------------------------
if os.path.exists("/mnt/block_volume"):
    BLOCK_STORAGE_PATH = "/mnt/block_volume/ecommerce.db"
else:
    BLOCK_STORAGE_PATH = os.path.join(os.getcwd(), "my_block_data", "ecommerce.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BLOCK_STORAGE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------------------
# MinIO (Object Storage)
# -------------------------------
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
    secure=False
)

BUCKET_NAME = "pes2ug23cs100"  # <-- your SRN

# -------------------------------
# Database Model
# -------------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_name = db.Column(db.String(120))


# -------------------------------
# Home Route
# -------------------------------
@app.route('/')
def home():
    return "E-commerce Lab is Running! Use POST /product and GET /products"


# -------------------------------
# Add Product (POST)
# -------------------------------
@app.route('/product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    image = request.files.get('image')

    if not image:
        return jsonify({"error": "No image uploaded"}), 400

    temp_path = image.filename
    image.save(temp_path)

    try:
        # Ensure bucket exists
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)

        # Metadata
        file_metadata = {
            "x-amz-meta-product-name": str(name),
            "x-amz-meta-product-price": str(price)
        }

        # Upload to MinIO
        minio_client.fput_object(
            BUCKET_NAME,
            image.filename,
            temp_path,
            metadata=file_metadata
        )

        # Store in DB (Block storage)
        new_product = Product(
            name=name,
            price=float(price),
            image_name=image.filename
        )
        db.session.add(new_product)
        db.session.commit()

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return jsonify({
        "status": "success",
        "msg": "Structured data in Block, Image in Object"
    })


# -------------------------------
# Get All Products (NEW 🔥)
# -------------------------------
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()

    minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")

    result = []
    for p in products:
        image_url = f"http://{minio_endpoint}/{BUCKET_NAME}/{p.image_name}"

        result.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "image_name": p.image_name,
            "image_url": image_url
        })

    return jsonify(result)


# -------------------------------
# Run App
# -------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    print("🚀 Flask app running at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)

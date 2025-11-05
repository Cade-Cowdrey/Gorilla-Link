#!/bin/bash
# Post-deployment script for Render
# This runs automatically after each deployment

echo "🚀 Running post-deployment tasks..."

# Run database migrations
echo "📦 Running database migrations..."
python -m flask db upgrade || echo "⚠️ Migrations skipped (may not exist yet)"

# Seed the database with real data
echo "🌱 Seeding database with REAL data..."
python seed_all_features.py

echo "✅ Post-deployment complete!"

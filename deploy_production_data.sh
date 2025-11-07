#!/bin/bash
# Quick deployment script to populate production database
# Run this on your Render server

echo "🚀 Deploying data to production..."
echo ""

# Run the seed script
python seed_data_simple.py

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Your production site now has:"
echo "  💰 20 Real Scholarships"
echo "  💼 20 Job Opportunities"
echo ""
echo "Visit your site to see the data:"
echo "  • https://gorilla-link.onrender.com/scholarships"
echo "  • https://gorilla-link.onrender.com/careers"

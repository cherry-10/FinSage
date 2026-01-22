# FinSage Deployment Guide

## 🚀 Deploying to Vercel

### Prerequisites
- GitHub account
- Vercel account (sign up at https://vercel.com)
- Backend API deployed and accessible

### Step 1: Prepare Your Repository

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

### Step 2: Configure Environment Variables

Create a `.env` file in the `frontend` directory with:

```env
VITE_API_URL=https://your-backend-api-url.com
```

**Important:** Replace `https://your-backend-api-url.com` with your actual backend API URL.

### Step 3: Deploy to Vercel

#### Option 1: Deploy via Vercel Dashboard (Recommended)

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure the project:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

4. Add Environment Variables:
   - Click "Environment Variables"
   - Add `VITE_API_URL` with your backend URL

5. Click "Deploy"

#### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   cd frontend
   vercel
   ```

4. **Follow the prompts:**
   - Set up and deploy? Yes
   - Which scope? Select your account
   - Link to existing project? No
   - Project name? finsage
   - Directory? ./
   - Override settings? No

5. **Add environment variables:**
   ```bash
   vercel env add VITE_API_URL
   ```
   Enter your backend API URL when prompted.

6. **Deploy to production:**
   ```bash
   vercel --prod
   ```

### Step 4: Update API Configuration

Update `frontend/src/services/api.js` to use environment variable:

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

### Step 5: Configure Backend CORS

Ensure your backend allows requests from your Vercel domain:

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-vercel-app.vercel.app",  # Add your Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 6: Verify Deployment

1. Visit your Vercel deployment URL
2. Test all features:
   - Login/Signup
   - Dashboard
   - Transactions
   - Budget
   - AI Insights
   - Profile

## 🔧 Troubleshooting

### Build Fails
- Check that all dependencies are in `package.json`
- Verify Node.js version compatibility
- Check build logs in Vercel dashboard

### API Connection Issues
- Verify `VITE_API_URL` environment variable is set correctly
- Check backend CORS configuration
- Ensure backend is accessible from Vercel

### Routing Issues
- Vercel automatically handles SPA routing with the configuration in `vercel.json`
- If 404 errors occur, check the rewrites configuration

## 📱 Custom Domain (Optional)

1. Go to your project in Vercel dashboard
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

## 🔄 Continuous Deployment

Vercel automatically deploys:
- **Production:** Every push to `main` branch
- **Preview:** Every pull request

To disable auto-deployment:
1. Go to Project Settings
2. Git → Ignored Build Step
3. Add custom logic

## 📊 Monitoring

- **Analytics:** Enable in Vercel dashboard
- **Logs:** View real-time logs in Vercel dashboard
- **Performance:** Check Web Vitals in Analytics tab

## 🛡️ Security Best Practices

1. **Never commit `.env` files**
2. **Use environment variables for sensitive data**
3. **Enable HTTPS only** (Vercel does this by default)
4. **Implement rate limiting on backend**
5. **Use secure authentication tokens**

## 📝 Post-Deployment Checklist

- [ ] All pages load correctly
- [ ] Authentication works
- [ ] API calls succeed
- [ ] Dark/Light theme works
- [ ] Mobile responsive design verified
- [ ] Footer displays on all pages
- [ ] Budget shows monthly spent correctly
- [ ] All AI features functional

## 🎉 Success!

Your FinSage application is now live on Vercel!

**Share your deployment URL:** `https://your-app-name.vercel.app`

---

For issues or questions, check:
- Vercel Documentation: https://vercel.com/docs
- Vite Documentation: https://vitejs.dev/guide/
- React Documentation: https://react.dev/

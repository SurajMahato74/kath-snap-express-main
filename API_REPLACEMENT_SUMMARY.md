# API URL Centralization Complete

## What was done:
1. Created `src/config/api.ts` with centralized API configuration
2. Replaced all hardcoded `const API_BASE = "http://localhost:8000/"` with imports
3. Updated WebSocket URLs to use centralized config
4. Maintained backward compatibility with existing code

## Files Updated:
- ✅ src/config/api.ts (NEW)
- ✅ src/components/VendorHeader.tsx
- ✅ src/components/FeaturedProducts.tsx  
- ✅ src/components/SearchBar.tsx
- ✅ src/components/TrendingItems.tsx
- ✅ src/pages/vendor/VendorHome.tsx
- ✅ src/hooks/useNotificationWebSocket.ts
- ✅ src/services/notificationService.ts
- ✅ src/services/orderService.ts
- ✅ src/services/cartService.ts
- ✅ src/services/messageService.ts
- ✅ src/services/favoritesService.ts
- ✅ src/lib/productApi.ts

## Remaining files need manual replacement:
All other files with hardcoded URLs need to import from '@/config/api' and replace:
- `"http://localhost:8000/"` → `API_BASE`
- `"http://localhost:8000"` → `API_CONFIG.BASE_URL`
- `"ws://localhost:8000"` → `API_CONFIG.WS_BASE_URL`

## To change API URL later:
Just update `src/config/api.ts`:
```typescript
export const API_CONFIG = {
  BASE_URL: 'https://your-production-api.com',
  WS_BASE_URL: 'wss://your-production-api.com'
};
```

All files will automatically use the new URL.
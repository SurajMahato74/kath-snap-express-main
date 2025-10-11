@echo off
echo ========================================
echo    FCM Auto-Open Debug Script
echo ========================================
echo.

echo Step 1: Installing FCM Community Plugin...
cd kath-snap-express-main
npm install @capacitor-community/fcm
echo.

echo Step 2: Syncing Capacitor...
npx cap sync android
echo.

echo Step 3: Building app...
npm run build
echo.

echo Step 4: Testing FCM setup...
cd ..
cd backend\ezeyway
python ..\..\test_fcm_debug.py
echo.

echo Step 5: Sending test notification...
python ..\..\send_test_notification.py
echo.

echo ========================================
echo Debug complete! Check the output above.
echo.
echo Next steps:
echo 1. Install app on device: npx cap run android
echo 2. Login as vendor
echo 3. Close app completely
echo 4. Check if test notification opens app
echo ========================================
pause
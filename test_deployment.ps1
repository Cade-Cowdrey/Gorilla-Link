# PowerShell Test Suite for PittState-Connect Deployment #31
# Tests all critical paths and verifies route fixes

$BaseURL = "https://pittstate-connect.onrender.com"
$Passed = 0
$Failed = 0
$Warnings = 0

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "PITTSTATE-CONNECT DEPLOYMENT #31 TEST SUITE" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Base URL: $BaseURL"
Write-Host "Testing deployment fixes for 18 template files..."
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

function Test-Endpoint {
    param(
        [string]$URL,
        [string]$TestName
    )
    
    try {
        Write-Host "Testing: $TestName..." -NoNewline
        $response = Invoke-WebRequest -Uri $URL -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host " ✅ PASS (Status: 200)" -ForegroundColor Green
            $script:Passed++
            return $response.Content
        }
        elseif ($response.StatusCode -ge 300 -and $response.StatusCode -lt 400) {
            Write-Host " ⚠️  WARN (Redirect: $($response.StatusCode))" -ForegroundColor Yellow
            $script:Warnings++
            return $null
        }
        else {
            Write-Host " ⚠️  WARN (Status: $($response.StatusCode))" -ForegroundColor Yellow
            $script:Warnings++
            return $null
        }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        
        if ($statusCode -eq 401) {
            Write-Host " ✅ PASS (401 - Auth required, route exists)" -ForegroundColor Green
            $script:Passed++
        }
        elseif ($statusCode -eq 404) {
            Write-Host " ❌ FAIL (404 - Route missing)" -ForegroundColor Red
            $script:Failed++
        }
        elseif ($statusCode -eq 500) {
            Write-Host " ❌ FAIL (500 - Server Error)" -ForegroundColor Red
            $script:Failed++
        }
        elseif ($statusCode) {
            Write-Host " ❌ FAIL (HTTP $statusCode)" -ForegroundColor Red
            $script:Failed++
        }
        else {
            Write-Host " ❌ FAIL (Connection error: $($_.Exception.Message))" -ForegroundColor Red
            $script:Failed++
        }
        return $null
    }
}

# 1. TEST HOMEPAGE & CORE ROUTES
Write-Host "`n📍 TEST 1: HOMEPAGE AND CORE ROUTES" -ForegroundColor Cyan
Write-Host "-" * 70
$homepageContent = Test-Endpoint "$BaseURL/" "Homepage (/)"

if ($homepageContent) {
    Write-Host "Checking for BuildError in homepage..." -NoNewline
    if ($homepageContent -match "BuildError|Could not build url") {
        Write-Host " ❌ FAIL (BuildError found)" -ForegroundColor Red
        $Failed++
    }
    else {
        Write-Host " ✅ PASS (No BuildError)" -ForegroundColor Green
        $Passed++
    }
    
    Write-Host "Checking for auth.register references..." -NoNewline
    if ($homepageContent -match "auth\.register|auth_bp\.register") {
        Write-Host " ❌ FAIL (auth.register still referenced)" -ForegroundColor Red
        $Failed++
    }
    else {
        Write-Host " ✅ PASS (No auth.register found)" -ForegroundColor Green
        $Passed++
    }
}

Test-Endpoint "$BaseURL/about" "About Page"

# 2. TEST AUTHENTICATION ROUTES
Write-Host "`n📍 TEST 2: AUTHENTICATION SYSTEM" -ForegroundColor Cyan
Write-Host "-" * 70
$loginContent = Test-Endpoint "$BaseURL/auth/login" "Login Page"

if ($loginContent) {
    Write-Host "Checking login page for register links..." -NoNewline
    if ($loginContent -match "auth\.register|auth_bp\.register") {
        Write-Host " ❌ FAIL (Register link still present)" -ForegroundColor Red
        $Failed++
    }
    else {
        Write-Host " ✅ PASS (No register links)" -ForegroundColor Green
        $Passed++
    }
}

Test-Endpoint "$BaseURL/auth/logout" "Logout Route"

# 3. TEST ALUMNI & NETWORKING
Write-Host "`n📍 TEST 3: ALUMNI AND NETWORKING" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/alumni" "Alumni Directory"
Test-Endpoint "$BaseURL/alumni/directory" "Alumni Directory Page"
Test-Endpoint "$BaseURL/mentors" "Mentors Hub"
Test-Endpoint "$BaseURL/connections" "Connections"

# 4. TEST STORIES SECTION (Fixed stories_bp -> stories)
Write-Host "`n📍 TEST 4: STORIES SECTION" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/stories" "Stories List"
Test-Endpoint "$BaseURL/stories/manage" "Stories Management"

# 5. TEST EVENTS (Fixed events_bp -> events)
Write-Host "`n📍 TEST 5: EVENTS SECTION" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/events" "Events Page"
Test-Endpoint "$BaseURL/events/upcoming" "Upcoming Events"

# 6. TEST COMMUNITY FEATURES
Write-Host "`n📍 TEST 6: COMMUNITY FEATURES" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/community" "Community Hub"
Test-Endpoint "$BaseURL/feed" "Community Feed"
Test-Endpoint "$BaseURL/groups" "Groups"
Test-Endpoint "$BaseURL/digests" "Digests"

# 7. TEST MESSAGING & NOTIFICATIONS (Fixed _bp suffixes)
Write-Host "`n📍 TEST 7: MESSAGING AND NOTIFICATIONS" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/messages" "Messages Inbox"
Test-Endpoint "$BaseURL/notifications" "Notifications Center"

# 8. TEST PROFILE & DASHBOARD
Write-Host "`n📍 TEST 8: PROFILE & DASHBOARD" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/profile" "Profile Page"
Test-Endpoint "$BaseURL/profile/dashboard" "Profile Dashboard"

# 9. TEST CAREERS & SCHOLARSHIPS
Write-Host "`n📍 TEST 9: CAREERS AND SCHOLARSHIPS" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/careers" "Careers Page"
Test-Endpoint "$BaseURL/scholarships" "Scholarships Page"

# 10. TEST ANALYTICS
Write-Host "`n📍 TEST 10: ANALYTICS DASHBOARD" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/analytics" "Analytics Dashboard"

# 11. TEST MENTORSHIP (Fixed mentorship_bp -> mentorship)
Write-Host "`n📍 TEST 11: MENTORSHIP SYSTEM" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/mentorship" "Mentorship Dashboard"

# 12. TEST DEPARTMENTS & FACULTY
Write-Host "`n📍 TEST 12: DEPARTMENTS AND FACULTY" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/departments" "Departments Page"

# 13. TEST OPPORTUNITIES
Write-Host "`n📍 TEST 13: OPPORTUNITIES" -ForegroundColor Cyan
Write-Host "-" * 70
Test-Endpoint "$BaseURL/opportunities" "Opportunities Page"

# SUMMARY
Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Total Passed:   $Passed" -ForegroundColor Green
Write-Host "Total Failed:   $Failed" -ForegroundColor Red
Write-Host "Total Warnings: $Warnings" -ForegroundColor Yellow

$total = $Passed + $Failed
if ($total -gt 0) {
    $successRate = ($Passed / $total) * 100
    $rate = [math]::Round($successRate, 1)
    if ($successRate -ge 90) {
        Write-Host "Success Rate:   $rate%" -ForegroundColor Green
    }
    elseif ($successRate -ge 70) {
        Write-Host "Success Rate:   $rate%" -ForegroundColor Yellow
    }
    else {
        Write-Host "Success Rate:   $rate%" -ForegroundColor Red
    }
}

Write-Host ("=" * 70) -ForegroundColor Cyan

if ($Failed -eq 0) {
    Write-Host "`n🎉 All tests passed! Deployment #31 is working correctly." -ForegroundColor Green
}
else {
    Write-Host "`n⚠️  Some tests failed. Review the results above." -ForegroundColor Yellow
}

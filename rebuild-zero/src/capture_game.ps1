param([Parameter(Mandatory=$true)][string]$OutputPath,[switch]$Activate)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ProwlerGameCapture {
 [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left,Top,Right,Bottom; }
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd,out RECT rect);
 [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd,int mode);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
'@
[ProwlerGameCapture]::SetProcessDPIAware() | Out-Null
$game=Get-Process -Name Titanfall2,NorthstarLauncher -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -eq 'Titanfall 2' } | Select-Object -First 1
if(-not $game){throw 'No Titanfall2 window is running'}
if($Activate){[ProwlerGameCapture]::ShowWindowAsync($game.MainWindowHandle,9) | Out-Null;[ProwlerGameCapture]::SetForegroundWindow($game.MainWindowHandle) | Out-Null;Start-Sleep -Milliseconds 700}
if([ProwlerGameCapture]::IsIconic($game.MainWindowHandle)){throw 'Game is minimized'}
if([ProwlerGameCapture]::GetForegroundWindow() -ne $game.MainWindowHandle){throw 'Game is not foreground; refusing to capture other applications'}
$rect=New-Object ProwlerGameCapture+RECT
if(-not [ProwlerGameCapture]::GetWindowRect($game.MainWindowHandle,[ref]$rect)){throw 'Cannot read game bounds'}
$width=$rect.Right-$rect.Left;$height=$rect.Bottom-$rect.Top
if($width -le 0 -or $height -le 0){throw 'Invalid game dimensions'}
$bitmap=New-Object Drawing.Bitmap($width,$height)
$graphics=[Drawing.Graphics]::FromImage($bitmap)
try { $graphics.CopyFromScreen($rect.Left,$rect.Top,0,0,$bitmap.Size);$bitmap.Save($OutputPath,[Drawing.Imaging.ImageFormat]::Png) } finally {$graphics.Dispose();$bitmap.Dispose()}
# A desktop/compositor can return stale or occluded pixels even when the HWND focus checks pass.
# Saving an image is not evidence that it contains a rendered game frame; inspect the image.
Write-Output "WINDOW_REGION_CAPTURE_UNVERIFIED $($game.Id) ${width}x${height} $OutputPath"

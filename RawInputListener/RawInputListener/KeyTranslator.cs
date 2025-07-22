﻿using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class KeyTranslator
{
    [DllImport("user32.dll")]
    static extern int ToUnicodeEx(uint wVirtKey, uint wScanCode, byte[] lpKeyState,
        [Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pwszBuff,
        int cchBuff, uint wFlags, IntPtr dwhkl);

    [DllImport("user32.dll")]
    static extern IntPtr GetKeyboardLayout(uint idThread);

    [DllImport("user32.dll")]
    static extern bool GetKeyboardState(byte[] lpKeyState);

    [DllImport("user32.dll")]
    static extern int GetKeyNameText(int lParam, StringBuilder lpString, int nSize);

    private static readonly Dictionary<uint, string> VirtualKeyNames = new()
    {
        { 0x08, "Backspace" },
        { 0x09, "Tab" },
        { 0x0D, "Enter" },
        { 0x10, "Shift" },
        { 0x11, "Ctrl" },
        { 0x12, "Alt" },
        { 0x13, "Pause" },
        { 0x14, "Caps Lock" },
        { 0x1B, "Esc" },
        { 0x20, "Space" },
        { 0x21, "Page Up" },
        { 0x22, "Page Down" },
        { 0x23, "End" },
        { 0x24, "Home" },
        { 0x25, "Left Arrow" },
        { 0x26, "Up Arrow" },
        { 0x27, "Right Arrow" },
        { 0x28, "Down Arrow" },
        { 0x2C, "Print Screen" },
        { 0x2D, "Insert" },
        { 0x2E, "Delete" },

        // 0–9
        { 0x30, "0" },
        { 0x31, "1" },
        { 0x32, "2" },
        { 0x33, "3" },
        { 0x34, "4" },
        { 0x35, "5" },
        { 0x36, "6" },
        { 0x37, "7" },
        { 0x38, "8" },
        { 0x39, "9" },

        // A–Z
        { 0x41, "A" }, { 0x42, "B" }, { 0x43, "C" }, { 0x44, "D" }, { 0x45, "E" },
        { 0x46, "F" }, { 0x47, "G" }, { 0x48, "H" }, { 0x49, "I" }, { 0x4A, "J" },
        { 0x4B, "K" }, { 0x4C, "L" }, { 0x4D, "M" }, { 0x4E, "N" }, { 0x4F, "O" },
        { 0x50, "P" }, { 0x51, "Q" }, { 0x52, "R" }, { 0x53, "S" }, { 0x54, "T" },
        { 0x55, "U" }, { 0x56, "V" }, { 0x57, "W" }, { 0x58, "X" }, { 0x59, "Y" },
        { 0x5A, "Z" },

        // Numpad
        { 0x60, "Num 0" }, { 0x61, "Num 1" }, { 0x62, "Num 2" }, { 0x63, "Num 3" },
        { 0x64, "Num 4" }, { 0x65, "Num 5" }, { 0x66, "Num 6" }, { 0x67, "Num 7" },
        { 0x68, "Num 8" }, { 0x69, "Num 9" }, { 0x6A, "Num *" }, { 0x6B, "Num +" },
        { 0x6C, "Separator" }, { 0x6D, "Num -" }, { 0x6E, "Num ." }, { 0x6F, "Num /" },

        // Function keys
        { 0x70, "F1" }, { 0x71, "F2" }, { 0x72, "F3" }, { 0x73, "F4" }, { 0x74, "F5" },
        { 0x75, "F6" }, { 0x76, "F7" }, { 0x77, "F8" }, { 0x78, "F9" }, { 0x79, "F10" },
        { 0x7A, "F11" }, { 0x7B, "F12" }, { 0x7C, "F13" }, { 0x7D, "F14" }, { 0x7E, "F15" },
        { 0x7F, "F16" }, { 0x80, "F17" }, { 0x81, "F18" }, { 0x82, "F19" }, { 0x83, "F20" },
        { 0x84, "F21" }, { 0x85, "F22" }, { 0x86, "F23" }, { 0x87, "F24" },

        // Lock / Modifier keys
        { 0x90, "Num Lock" },
        { 0x91, "Scroll Lock" },
        { 0xA0, "Left Shift" }, { 0xA1, "Right Shift" },
        { 0xA2, "Left Ctrl" },  { 0xA3, "Right Ctrl" },
        { 0xA4, "Left Alt" },   { 0xA5, "Right Alt" },

        // Browser & media keys
        { 0xA6, "Browser Back" }, { 0xA7, "Browser Forward" }, { 0xA8, "Browser Refresh" },
        { 0xA9, "Browser Stop" }, { 0xAA, "Browser Search" }, { 0xAB, "Browser Favorites" },
        { 0xAC, "Browser Home" },
        { 0xAD, "Volume Mute" }, { 0xAE, "Volume Down" }, { 0xAF, "Volume Up" },
        { 0xB0, "Next Track" }, { 0xB1, "Previous Track" }, { 0xB2, "Stop Media" },
        { 0xB3, "Play/Pause" }, { 0xB4, "Launch Mail" }, { 0xB5, "Launch Media Player" },
        { 0xB6, "Launch App 1" }, { 0xB7, "Launch App 2" },

        // OEM / misc
        { 0xBA, ";" }, { 0xBB, "=" }, { 0xBC, "," }, { 0xBD, "-" }, { 0xBE, "." },
        { 0xBF, "/" }, { 0xC0, "`" }, { 0xDB, "[" }, { 0xDC, "\\" }, { 0xDD, "]" }, { 0xDE, "'" }
    };

    public static string GetKeyName(uint virtualKey, uint scanCode)
    {
        // Use fallback table first for known non-character keys
        if (VirtualKeyNames.TryGetValue(virtualKey, out var fallbackName))
            return fallbackName;

        // Try ToUnicodeEx for printable characters
        byte[] keyboardState = new byte[256];
        GetKeyboardState(keyboardState);

        var sb = new StringBuilder(64);
        var layout = GetKeyboardLayout(0);
        int result = ToUnicodeEx(virtualKey, scanCode, keyboardState, sb, sb.Capacity, 0, layout);
        if (result > 0 && sb.Length > 0)
            return sb.ToString();

        // Try GetKeyNameText if that fails
        int lParam = (int)((scanCode << 16) | (1 << 24));
        var nameSb = new StringBuilder(64);
        if (GetKeyNameText(lParam, nameSb, nameSb.Capacity) > 0)
            return nameSb.ToString();

        // Final fallback
        return $"VK_{virtualKey:X2}";
    }
}

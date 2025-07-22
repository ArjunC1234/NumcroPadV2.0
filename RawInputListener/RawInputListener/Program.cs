using Linearstar.Windows.RawInput;
using Linearstar.Windows.RawInput.Native;
using System;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

class Program
{
    [STAThread]
    static void Main()
    {
        var window = new RawInputReceiverWindow();

        window.Input += (sender, e) =>
        {
            var data = e.Data;

            if (data is RawInputKeyboardData keyboardData)
            {
                var keyboard = keyboardData.Keyboard;

                var keyEvent = new
                {
                    timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
                    device = keyboardData.Device?.DevicePath,
                    product = keyboardData.Device?.ProductName,
                    vendorId = keyboardData.Device?.VendorId,
                    productId = keyboardData.Device?.ProductId,
                    vk = (int)keyboard.VirutalKey,
                    scan = keyboard.ScanCode,
                    flags = keyboard.Flags.ToString(),
                    eventType = keyboard.Flags.HasFlag(RawKeyboardFlags.Up) ? "up" : "down",
                    keyName = KeyTranslator.GetKeyName((uint)keyboard.VirutalKey, (uint)keyboard.ScanCode)
                };

                string json = JsonSerializer.Serialize(keyEvent);
                Console.WriteLine(json);
            }
        };

        RawInputDevice.RegisterDevice(HidUsageAndPage.Keyboard,
            RawInputDeviceFlags.ExInputSink | RawInputDeviceFlags.NoLegacy, window.Handle);

        Console.WriteLine("Listening for key input...");
        Application.Run();

        RawInputDevice.UnregisterDevice(HidUsageAndPage.Keyboard);
    }
}

using System;
using Linearstar.Windows.RawInput;

class RawInputEventArgs : EventArgs
{
    public RawInputEventArgs(RawInputData data)
    {
        Data = data;
    }

    public RawInputData Data { get; }
}

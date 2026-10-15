namespace Agent;

/// <summary>Refuses a call that carries no valid key, before any handler sees it.</summary>
/// <remarks>
/// Implements: DSN-SVC-01
/// </remarks>
public static class KeyCheck
{
    /// <summary>Whether a call carrying <paramref name="key"/> may go on.</summary>
    public static bool Admits(string? key, string expected) =>
        !string.IsNullOrEmpty(key) && key == expected;
}

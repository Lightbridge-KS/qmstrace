using FluentAssertions;

namespace Agent.Tests.Unit;

/// <summary>The agent's side of the key check.</summary>
public class KeyCheckTests
{
    [Fact(DisplayName = "TC-SVC-01.1 a call without a key is refused")]
    public void Admits_NoKey_IsFalse()
    {
        KeyCheck.Admits(null, "the-key").Should().BeFalse();
    }

    [Theory(DisplayName = "TC-SVC-01.2 the key check decides before any handler")]
    [InlineData("the-key", true)]
    [InlineData("a-wrong-key", false)]
    public void Admits_AnyKey_DecidesAlone(string key, bool admitted)
    {
        KeyCheck.Admits(key, "the-key").Should().Be(admitted);
    }
}

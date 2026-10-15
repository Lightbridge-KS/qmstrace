using FluentAssertions;

namespace Agent.Probe;

// Each probe asks one question: how do xUnit and TRX treat this shape? The answer, read from
// the TRX file, decides what the extractor must do with it. IDs TC-BAG-90.x are probe-only.

public class Shapes
{
    private const string Id = "TC-BAG-90.4";

    [Fact]
    public void NoDisplayName_Runs() => true.Should().BeTrue();

    [Fact(DisplayName = Id + " from a const and a concatenation")]
    public void ConstConcatenation_Runs() => true.Should().BeTrue();

    [Fact(DisplayName = $"{Id} from a constant interpolated string")]
    public void ConstInterpolation_Runs() => true.Should().BeTrue();

    [Fact(DisplayName = """TC-BAG-90.5 from a raw string literal""")]
    public void RawString_Runs() => true.Should().BeTrue();

    [Fact(DisplayName = @"TC-BAG-90.6 from a verbatim ""quoted"" string")]
    public void VerbatimString_Runs() => true.Should().BeTrue();

    [Fact(DisplayName = "TC-BAG-90.7 skipped", Skip = "probe: how a skip is reported")]
    public void Skipped_IsNotRun() => true.Should().BeFalse();

    [Fact(DisplayName = "TC-BAG-90.8 async")]
    public async Task Async_Runs()
    {
        await Task.Yield();
        true.Should().BeTrue();
    }

    [Fact(DisplayName = "TC-BAG-90.9 with a trait"), Trait("verifies", "REQ-BAG-01")]
    public void WithTrait_Runs() => true.Should().BeTrue();

    [Xunit.FactAttribute(DisplayName = "TC-BAG-90.10 fully qualified attribute")]
    public void FullyQualified_Runs() => true.Should().BeTrue();

    [Theory(DisplayName = "TC-BAG-90.11 member data")]
    [MemberData(nameof(Rows))]
    public void MemberData_Runs(int value, string label) =>
        label.Should().NotBeNull(value.ToString());

    public static TheoryData<int, string> Rows =>
        new() { { 1, "one" }, { 2, "two, with a comma" } };

    [Theory(DisplayName = "TC-BAG-90.12 one row fails")]
    [InlineData(1)]
    [InlineData(2)]
    public void OneRowFails(int value) => value.Should().Be(1);

    [SlowFact(DisplayName = "TC-BAG-90.13 custom fact attribute")]
    public void CustomAttribute_Runs() => true.Should().BeTrue();

#if NEVER_DEFINED
    [Fact(DisplayName = "TC-BAG-90.14 compiled out")]
    public void CompiledOut() => true.Should().BeTrue();
#endif

    // [Fact(DisplayName = "TC-BAG-90.15 commented out")]
    public void CommentedOut() => true.Should().BeTrue();

    public class Nested
    {
        [Fact(DisplayName = "TC-BAG-90.16 nested class")]
        public void Nested_Runs() => true.Should().BeTrue();
    }
}

public sealed class SlowFactAttribute : FactAttribute;

public abstract class InheritedBase
{
    [Fact(DisplayName = "TC-BAG-90.17 declared on an abstract base")]
    public void Inherited_Runs() => true.Should().BeTrue();
}

public class FirstDerived : InheritedBase;

public class SecondDerived : InheritedBase;

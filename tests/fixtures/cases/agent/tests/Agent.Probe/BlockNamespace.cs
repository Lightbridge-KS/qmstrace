using FluentAssertions;

namespace Agent.Probe.Blocks
{
    public class InABlockNamespace
    {
        [Fact(DisplayName = "TC-BAG-90.18 block-scoped namespace")]
        public void Block_Runs() => true.Should().BeTrue();
    }
}

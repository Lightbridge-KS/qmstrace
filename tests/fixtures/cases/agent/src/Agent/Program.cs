// The agent's entry point, written as top-level statements: it declares no type, so it is
// marked here, in the comment the file opens with.
//
// Implements: DSN-SVC-01

var expected = Environment.GetEnvironmentVariable("AGENT_KEY") ?? "";
var admitted = Agent.KeyCheck.Admits(args.Length > 0 ? args[0] : null, expected);
Console.WriteLine(admitted ? "admitted" : "refused");
return admitted ? 0 : 1;

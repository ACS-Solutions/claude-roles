---
name: dotnet
description: .NET specifics (Serilog, Microsoft.Extensions.Logging, OpenTelemetry, ASP.NET Core, Options, HttpClientFactory) for the cross-cutting concerns rules in xcut:standards. Use alongside xcut:standards when writing or reviewing logging, telemetry, error handling, configuration or resilience in C# code.
---

# .NET specifics for cross-cutting concerns

How the generic rules show up in .NET code. House rules still win.

## Logging

- **LOG1**: `logger.LogInformation($"Order {id}")` and `Log.Information("Order " + id)` break structure (analyzer CA2254). Use `"Order {OrderId}"`. For hot paths with `ILogger`, `[LoggerMessage]` source-generated methods avoid boxing and template parsing.
- **LOG1**: Serilog `{@Value}` destructures an object, so check that the object has no secrets and is not huge. `{Value:l}` renders a string without quotes.
- **LOG3**: `ILogger.BeginScope(...)` or Serilog `LogContext.PushProperty(...)` / `Log.ForContext(...)` carry context. ASP.NET Core adds `TraceId`/`SpanId` to scopes when `IncludeScopes` is on, and with Serilog `Enrich.FromLogContext()` is needed.
- **LOG4**: Exception messages from Azure SDKs, SqlClient and HttpClient can contain connection strings, SAS tokens or query strings. `ex.ToString()` includes inner exceptions and sometimes request URIs. Logging `IConfiguration` wholesale, or `Environment.GetEnvironmentVariables()`, leaks secrets.
- **LOG5**: With `ILogger`, pass the exception as the first argument, `LogError(ex, "...")`, unless house rules prescribe a redacted text form instead. `catch (Exception ex) { _logger.LogError(ex, ...); throw; }` repeated at several layers is LOG5.
- **LOG6**: `logger.IsEnabled(LogLevel.Debug)` guards expensive argument construction. Serilog has `Log.IsEnabled(LogEventLevel.Debug)`.
- **LOG8**: Serilog static `Log` needs `Log.CloseAndFlush()` / `CloseAndFlushAsync()` in `finally`, or logs written just before exit are lost. A bootstrap logger before configuration is loaded is the usual pattern.
- **LOG9**: `Environment.GetEnvironmentVariable("JOURNAL_STREAM") != null` alone is LOG9. .NET has no managed `fstat`. On Linux the simple check reads the link target of `/proc/self/fd/1` (or `2`), for example `new FileInfo("/proc/self/fd/1").LinkTarget`, which is `socket:[<inode>]` for the journal, and compares that inode with the one in `JOURNAL_STREAM`. Comparing the inode alone is acceptable because every socket is on the same sockfs device. A full `device:inode` comparison needs `fstat` through P/Invoke or `Mono.Unix`.

## Telemetry

- **TEL1**: OpenTelemetry .NET uses `System.Diagnostics.ActivitySource` for spans. `AddAspNetCoreInstrumentation`, `AddHttpClientInstrumentation` and `AddSqlClientInstrumentation` (or EF Core's) cover the common boundaries. Custom spans use `using var activity = Source.StartActivity("Name")`; `activity?.SetStatus(ActivityStatusCode.Error)` marks a failure. Azure Service Bus and Event Hubs propagate context through `Diagnostic-Id`/`traceparent` application properties.
- **TEL1**: Application Insights (classic SDK or Azure Monitor OpenTelemetry distro): check that only one is in use, and that `TelemetryClient.TrackException` and `ILogger` are not both reporting the same failure.
- **TEL2**: `System.Diagnostics.Metrics.Meter` with `Counter<T>` / `Histogram<T>`; tags on `Add`/`Record` must be low-cardinality.
- **TEL3**: `AddHealthChecks()` with `MapHealthChecks("/health/live")` / `"/health/ready"` and tags to separate the two.
- **TEL4**: `ResourceBuilder.CreateDefault().AddService(name, serviceVersion: ...)`, or Serilog `Enrich.WithProperty("Application", ...)` from configuration.

## Error handling

- **ERR1**: `catch { }` and `catch (Exception) { }` with no comment.
- **ERR2**: ASP.NET Core boundaries are `UseExceptionHandler` / `IExceptionHandler` with `AddProblemDetails()`; controllers and endpoints should not each wrap everything in try/catch.
- **ERR3**: `catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)` is the precise form. A bare `catch (OperationCanceledException)` also hides `HttpClient` timeouts, which throw `TaskCanceledException` without the caller's token being cancelled.
- **ERR4**: Console apps return documented exit codes from `Main`. Web APIs return `ProblemDetails` / `ValidationProblemDetails`.
- **ERR5**: `async void` (other than event handlers), `_ = SomeAsync()` and `Task.Run` without a catch inside, and `ContinueWith` that ignores a faulted antecedent. `BackgroundService.ExecuteAsync` exceptions stop the host by default (`BackgroundServiceExceptionBehavior.StopHost`), which must be a conscious choice.

## Configuration

- **CFG1**: `services.AddOptions<T>().BindConfiguration(...).ValidateDataAnnotations().ValidateOnStart()` or a source-generated `[OptionsValidator]`. `IOptions<T>.Value` read lazily means validation errors surface at first use, not at startup.
- **CFG2**: secrets in `appsettings*.json`, `launchSettings.json` or test configuration committed to git. User secrets, environment variables, Key Vault (`AddAzureKeyVault`), managed identity or a credential store are the alternatives.

## Resilience

- **RES1**: `HttpClient` default timeout is 100 s, and `new HttpClient()` per call exhausts sockets; use `IHttpClientFactory`. `SqlCommand.CommandTimeout` defaults to 30 s. SDK clients each have their own retry/timeout options.
- **RES2**: `Microsoft.Extensions.Http.Resilience` (`AddStandardResilienceHandler`) or Polly. Retrying POSTs that are not idempotent is RES2.
- **RES3**: `using` / `await using` on `IDisposable` / `IAsyncDisposable`. Linked `CancellationTokenSource`s must be disposed.
- **RES4**: Generic Host `HostOptions.ShutdownTimeout`; console apps handle `PosixSignalRegistration` or `Console.CancelKeyPress`.

## Dependencies

- Before calling a package reference unused or speculative, check whether it is also transitive: `dotnet list package --include-transitive`, the project's `obj/project.assets.json`, or the referencing package's `.nuspec` under `~/.nuget/packages/<id>/<version>/`. A direct `PackageReference` (or a `Directory.Packages.props` entry) to a package that is already transitive is normally a version pin, often to lift a vulnerable version, and is not a finding.

/// Failures a screen can show. Anything that means "the server isn't there" is
/// [Unreachable] (render the can't-reach state, never an empty list); only a 404 is
/// [NotFound].
sealed class ApiFailure implements Exception {
  const ApiFailure();
}

/// The backend didn't answer at [address] (refused, timed out, no route).
class Unreachable extends ApiFailure {
  const Unreachable(this.address);
  final String address;
  @override
  String toString() => "Can't reach the pokérag server at $address";
}

class NotFound extends ApiFailure {
  const NotFound();
}

/// The backend answered with an error other than 404.
class ServerError extends ApiFailure {
  const ServerError(this.status);
  final int? status;
}

/// The server refused a write (422) and said why, e.g. an illegal move for the species.
class Rejected extends ApiFailure {
  const Rejected(this.reason);
  final String reason;
  @override
  String toString() => reason;
}

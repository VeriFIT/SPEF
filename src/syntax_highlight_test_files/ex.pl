
use IO::Socket;

$socket = IO::Socket::INET->new
(
    PeerAddr => 'server.com',
    PeerPort => 1247,
    Proto    => "tcp",
    Type     => SOCK_STREAM
) or die "Could not create client.\n";

unless (defined($child_pid = fork())) {die "Can not fork.\n"};

if ($child_pid) {
    while ($line = <>) {
        print $socket $line;
    }
} else {
    while($line = <$socket>) {
        print "Read this from server: $line";
    }
}

   
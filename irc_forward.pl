# Copyright (c) 2010 Adam James <atj@pulsewidth.org.uk>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

use strict;
use vars qw($VERSION %IRSSI);

use Irssi;
use POSIX qw(strftime);
use LWP::UserAgent;
use JSON

$VERSION = '0.5';
%IRSSI = (
	authors => 'Joseph Hajduk',
	contact => 'joseph@solidys.com',
	url => '',
	name => 'irc_forward',
	description =>
		"forwards pms from FleetBot through thumperbot",
	license => 'MIT',
);

my $msgs = {};

# check the message log every 15 seconds
Irssi::timeout_add(15*1000, 'check_messages', '');

sub handle_privmsg() {
	my ($server, $message, $user, $address, $target) = @_;

	unless ($user == "FleetBot") {
		return;
	}

	add_privmsg($server, $message, $user, $address);
}

sub check_messages() {
	if (scalar(keys(%{$msgs})) > 0) {
		send_ping();
		$msgs = {};
	}

	return 0;
}

sub add_privmsg() {
	my ($server, $message, $user, $addr) = @_;

	unless (defined $msgs->{$server->{chatnet}}) {
		$msgs->{$server->{chatnet}} = {};
	};

	unless (defined $msgs->{$server->{chatnet}}{$user}) {
		$msgs->{$server->{chatnet}}->{$user} = [];
	};

	push(@{$msgs->{$server->{chatnet}}->{$user}},
		[time, $message]
	);
}

sub generate_ping() {
	my @lines = ();

	if (scalar(keys(%{$msgs})) == 0) {
		return undef;
	}

	for my $network (keys %{$msgs}) {
		for my $user (keys %{$msgs->{$network}}) {
			for my $ele (@{$msgs->{$network}->{$user}}) {
				push(@lines, sprintf("{'time'='[%s]', 'sender'='<%s>', message='%s'}",
					strftime("%T", encode_json(localtime($ele->[0]))),
					encode_json($user),
					encode_json($ele->[1]))
				);
			}
			push(@lines, '');
		}
	}

	return \@lines;
}

sub send_ping() {
    my $body = generate_ping();

	unless (defined($body)) {
		return;
	}

    LWP::UserAgent->new()->post(
      "http://localhost:8080/pf/parse", [
      "messages" => "[" . join(",", @{$body}) . "]",
     ]);
}

Irssi::signal_add_last("message private", "handle_privmsg");

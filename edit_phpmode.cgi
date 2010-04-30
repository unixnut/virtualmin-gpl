#!/usr/local/bin/perl
# Show web and PHP options for a virtual server

require './virtual-server-lib.pl';
&ReadParse();
$d = &get_domain($in{'dom'});
&can_edit_domain($d) || &error($text{'edit_ecannot'});
$can = &can_edit_phpmode($d);
$can || &error($text{'phpmode_ecannot'});
if (!$d->{'alias'}) {
	@modes = &supported_php_modes($d);
	$mode = &get_domain_php_mode($d);
	}

# Make sure an Apache virtualhost exists, or else all the rest is pointless
($virt, $vconf) = &get_apache_virtual($d->{'dom'}, $d->{'web_port'});
$virt || &error(&text('phpmode_evirt', $d->{'dom'}, $d->{'web_port'}));

&ui_print_header(&domain_in($d), $text{'phpmode_title'}, "");

print &ui_form_start("save_phpmode.cgi");
print &ui_hidden("dom", $d->{'id'}),"\n";
print &ui_hidden_table_start($text{'phpmode_header'}, "width=100%", 2,
			     "phpmode", 1, [ "width=30%" ]);

if (!$d->{'alias'} && $can == 2) {
	# Use suexec
	print &ui_table_row(&hlink($text{'phpmode_suexec'}, "phpmode_suexec"),
			    &ui_yesno_radio("suexec", &get_domain_suexec($d)));
	}

if (!$d->{'alias'} && $can == 2) {
	# PHP execution mode
	print &ui_table_row(&hlink($text{'phpmode_mode'}, "phpmode"),
			    &ui_radio("mode", $mode,
			      [ map { [ $_, $text{'phpmode_'.$_}."<br>" ] }
				    @modes ]));
	}

# PHP fcgi sub-processes
if (!$d->{'alias'} && &indexof("fcgid", @modes) >= 0 && $can == 2) {
	$children = &get_domain_php_children($d);
	if ($children > 0) {
		print &ui_table_row(&hlink($text{'phpmode_children'},
					   "phpmode_children"),
				    &ui_opt_textbox("children", $children || '',
					 5, $text{'tmpl_phpchildrennone'}));
		}
	}

# PHP max execution time, for fcgi mode
if (!$d->{'alias'} && &indexof("fcgid", @modes) >= 0) {
	$max = $mode eq "fcgid" ? &get_fcgid_max_execution_time($d)
				: &get_php_max_execution_time($d);
	print &ui_table_row(&hlink($text{'phpmode_maxtime'}, "phpmode_maxtime"),
			    &ui_opt_textbox("maxtime", $max, 5,
					    $text{'form_unlimit'})." ".
			    $text{'rfile_secs'});
	}

# Ruby execution mode
if (defined(&supported_ruby_modes)) {
	@rubys = &supported_ruby_modes($d);
	if (!$d->{'alias'} && @rubys && $can == 2) {
		print &ui_table_row(
			&hlink($text{'phpmode_rubymode'}, "rubymode"),
			&ui_radio("rubymode", &get_domain_ruby_mode($d),
				  [ [ "", $text{'phpmode_noruby'}."<br>" ],
				    map { [ $_, $text{'phpmode_'.$_}."<br>" ] }
					@rubys ]));
		}
	}

# Write logs via program. Don't show unless enabled.
if ((!$d->{'alias'} || $d->{'alias_mode'} != 1) && $can == 2 &&
    &get_writelogs_status($d)) {
	print &ui_table_row(
		&hlink($text{'newweb_writelogs'}, "template_writelogs"),
		&ui_yesno_radio("writelogs", &get_writelogs_status($d)));
	}

# Match all sub-domains
print &ui_table_row(&hlink($text{'phpmode_matchall'}, "matchall"),
		    &ui_yesno_radio("matchall", &get_domain_web_star($d)));

# Default website for its IP
if (!$d->{'alias'} || $d->{'alias_mode'} != 1) {
	($defvirt, $defd) = &get_default_website($d);
	$defweb = $defd && $defd->{'id'} eq $d->{'id'} ? 1 : 0;
	$defno = $defd ? &text('phpmode_defno', $defd->{'dom'}) : $text{'no'};
	if (&can_default_website($d) && !$defweb) {
		print &ui_table_row(&hlink($text{'phpmode_defweb'}, "defweb"),
			&ui_radio("defweb", $defweb,
				  [ [ 1, $text{'yes'} ], [ 0, $defno ] ]));
		}
	else {
		print &ui_table_row(&hlink($text{'phpmode_defweb'}, "defweb"),
			$defweb ? $text{'yes'} : $defno);
		}
	}

# Log file locations
if (!$d->{'alias'} && &can_log_paths()) {
	$alog = &get_apache_log($d->{'dom'}, $d->{'web_port'}, 0);
	if ($alog) {
		print &ui_table_row(&hlink($text{'phpmode_alog'}, 'accesslog'),
			&ui_textbox("alog", $alog, 60));
		}
	$elog = &get_apache_log($d->{'dom'}, $d->{'web_port'}, 1);
	if ($elog) {
		print &ui_table_row(&hlink($text{'phpmode_elog'}, 'errorlog'),
			&ui_textbox("elog", $elog, 60));
		}
	}

print &ui_hidden_table_end();

# Show PHP information
if (defined(&list_php_modules) && !$d->{'alias'}) {
	print &ui_hidden_table_start($text{'phpmode_header2'}, "width=100%",
				     2, "phpinfo", 0, [ "width=30%" ]);

	# PHP modules for the domain
	foreach $phpver (&list_available_php_versions($d)) {
		@mods = &list_php_modules($d, $phpver->[0], $phpver->[1]);
		@mods = sort { lc($a) cmp lc($b) } @mods;
		print &ui_table_row(&text('phpmode_mods', $phpver->[0]),
			&ui_grid_table([ map { "<tt>$_</tt>" } @mods ],
				       6, 100));
		}

	# Pear modules
	if (&foreign_check("php-pear")) {
		&foreign_require("php-pear", "php-pear-lib.pl");
		@allmods = ( );
		if (defined(&php_pear::list_installed_pear_modules)) {
			@allmods = &php_pear::list_installed_pear_modules();
			}
		foreach $cmd (&php_pear::get_pear_commands()) {
			@mods = grep { $_->{'pear'} == $cmd->[1] } @allmods;
			@mods = sort { lc($a->{'name'}) cmp lc($b->{'name'}) }
				     @mods;
			if (@mods) {
				print &ui_table_row(
				    &text('phpmode_pears', $cmd->[1]),
				    &ui_grid_table(
				      [ map { "<tt>$_->{'name'}</tt>" } @mods ], 6, 100));
				}
			}
		}

	print &ui_hidden_table_end();
	}

print &ui_form_end([ [ "save", $text{'save'} ] ]);

&ui_print_footer(&domain_footer_link($d),
		 "", $text{'index_return'});


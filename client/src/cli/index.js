#!/usr/bin/env node
var cli = require('yargs');

cli
  .usage('Usage: $0 <command> [options]')
  .help('help');

cli
  .command(
    'scaffold <name>',
    'scaffold out a wagtail component',
    require('./scaffold'));

cli
  .argv;

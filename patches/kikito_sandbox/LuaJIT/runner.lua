local sandbox = require 'sandbox'
sandbox.run(io.read('*a'), { env = { print = print }}) -- read the .lua file from the standard input
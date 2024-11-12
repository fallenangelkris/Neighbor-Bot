/Neighbor-Bot
  /config
    - config.json      # Configuration file for the bot, contains API keys and settings.
  /commands
    - general.js       # General commands like !hello, !help, etc.
    - admin.js         # Admin-related commands such as !ban, !kick.
  /events
    - ready.js         # Code for when the bot is ready and online.
    - message.js       # Code for handling messages and interactions.
  /utils
    - helpers.js       # Helper functions used across commands and events.
  /logs
    - bot.log          # Log files for troubleshooting.
  - bot.js             # Main entry point for the bot.
  - package.json       # Node.js package manager file with dependencies.

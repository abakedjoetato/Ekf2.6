# Emerald's Killfeed - Complete User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Premium Features](#premium-features)
3. [Economy System](#economy-system)
4. [Casino Games](#casino-games)
5. [Faction Warfare](#faction-warfare)
6. [Leaderboards](#leaderboards)
7. [Statistics & Tracking](#statistics--tracking)
8. [Server Configuration](#server-configuration)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

Emerald's Killfeed is an advanced Discord bot designed for gaming communities, offering real-time server monitoring, faction warfare systems, economy features, and comprehensive player statistics.

### Basic Commands
- `/help` - Display available commands
- `/stats player <name>` - View player statistics
- `/leaderboard` - View server leaderboards
- `/server status` - Check server status

---

## Premium Features

Premium features unlock the full potential of Emerald's Killfeed with advanced economy, casino games, and faction management.

### Subscription Management
**Available to: Server Administrators**

- `/subscription status` - Check current premium status for your server
- `/subscription activate` - Activate premium features (Admin only)
- `/subscription deactivate` - Deactivate premium features (Admin only)

### Premium Benefits
- Economy system with wallets and transactions
- Professional casino games
- Advanced faction management
- Automated leaderboard updates
- Enhanced statistics tracking
- Custom bounty system

---

## Economy System
**Requires: Premium Subscription**

The economy system provides a comprehensive virtual currency experience for your community.

### Wallet Management
- `/wallet` - View your current balance
- `/wallet daily` - Claim daily bonus (once per 24 hours)
- `/wallet work` - Earn money through work commands
- `/wallet transfer <user> <amount>` - Send money to another user

### Earning Money
- **Daily Bonus**: $500 every 24 hours
- **Work Commands**: $50-200 per use (cooldown applies)
- **Casino Winnings**: Variable based on games played
- **Faction Rewards**: Bonus payments for faction activities

### Starting Balance
All new users begin with $1,000 in their wallet.

---

## Casino Games
**Requires: Premium Subscription**

Experience professional casino games with interactive interfaces and real money betting.

### Available Games

#### Slot Machine
- `/casino slots <bet_amount>` - Play slot machine
- **Minimum Bet**: $10
- **Maximum Bet**: $10,000
- **Payouts**: Various combinations with different multipliers

#### Blackjack
- `/casino blackjack <bet_amount>` - Play blackjack against the house
- **Objective**: Get as close to 21 without going over
- **House Rules**: Dealer stands on 17
- **Blackjack Payout**: 3:2

#### Roulette
- `/casino roulette <bet_amount> <bet_type>` - Play roulette
- **Bet Types**: 
  - Red/Black (1:1 payout)
  - Odd/Even (1:1 payout)
  - Single Number (35:1 payout)
  - Dozens (2:1 payout)

#### Dice Games
- `/casino dice <bet_amount>` - Roll dice for various outcomes
- **High/Low**: Bet on roll being above or below 7
- **Specific Number**: Bet on exact dice total

### Casino Interface Features
- **Interactive Buttons**: Click to make game decisions
- **Betting Modals**: Secure bet amount entry
- **Real-time Results**: Instant game outcomes
- **Balance Tracking**: Live wallet updates

---

## Faction Warfare
**Requires: Premium Subscription**

Create or join factions to compete with other groups in organized warfare.

### Faction Management

#### Creating a Faction
- `/faction create` - Opens faction creation interface
- **Requirements**: 
  - Faction name (3-32 characters)
  - Optional faction tag (2-6 characters)
  - Optional description (up to 500 characters)
  - Creation cost: $10,000

#### Joining a Faction
- `/faction join` - View available factions to join
- `/faction leave` - Leave your current faction
- **Note**: Leaving a faction has a 24-hour cooldown before joining another

### Faction Features

#### Leadership Roles
- **Leader**: Full faction control and management
- **Officers**: Can invite members and manage basic settings
- **Members**: Standard faction participants

#### Faction Commands
- `/faction info` - View detailed faction information
- `/faction members` - List all faction members
- `/faction stats` - View faction performance statistics
- `/faction invite <user>` - Invite a user to join (Officers+)
- `/faction kick <user>` - Remove a member (Officers+)
- `/faction promote <user>` - Promote member to officer (Leader only)
- `/faction settings` - Configure faction settings (Leader only)

#### Faction Statistics
- **Total Kills**: Combined kills by all faction members
- **Total Deaths**: Combined deaths by all faction members
- **K/D Ratio**: Overall faction kill/death ratio
- **Member Count**: Active and inactive member tracking
- **Activity Level**: Faction engagement metrics

### Faction Warfare
- **Territory Control**: Compete for server dominance
- **Faction vs Faction**: Organized battles and competitions
- **Reward System**: Bonuses for faction achievements
- **Rankings**: Server-wide faction leaderboards

---

## Leaderboards
**Basic: Limited | Premium: Full Featured**

Track and display top performers across various categories.

### Leaderboard Categories
- **Kills**: Most eliminations
- **Deaths**: Highest death count
- **K/D Ratio**: Best kill/death ratios
- **Distance**: Longest elimination distances
- **Weapons**: Most used weapons
- **Factions**: Top-performing factions

### Viewing Leaderboards
- `/leaderboard` - Display main leaderboard interface
- **Time Filters**:
  - All Time
  - This Month
  - This Week
  - Today
- **Navigation**: Previous/Next buttons for pagination
- **Interactive Interface**: Dropdown menus for category selection

### Automated Updates
**Premium Feature**: Leaderboards automatically update every 30 minutes with fresh data.

---

## Statistics & Tracking

Comprehensive player and server statistics tracking with detailed analytics.

### Player Statistics
- `/stats player <name>` - View detailed player stats
- **Tracking Includes**:
  - Total kills and deaths
  - K/D ratio calculations
  - Weapon usage statistics
  - Distance records
  - Faction affiliations
  - Recent activity

### Cross-Character Linking
- `/link player <main> <alt>` - Link alternate characters
- **Benefits**:
  - Combined statistics across characters
  - Unified leaderboard entries
  - Comprehensive activity tracking

### Advanced Analytics
**Premium Feature**:
- **Trend Analysis**: Performance over time
- **Weapon Preferences**: Detailed weapon statistics
- **Activity Patterns**: Play time analysis
- **Comparative Stats**: Rankings relative to other players

---

## Server Configuration

Configure bot settings and manage server-specific features.

### Basic Configuration
**Available to: Server Administrators**

#### Channel Setup
- `/admin channels killfeed <channel>` - Set killfeed channel
- `/admin channels leaderboard <channel>` - Set leaderboard channel
- `/admin channels stats <channel>` - Set statistics channel

#### Server Management
- `/admin server add <name> <ip>` - Add server for monitoring
- `/admin server remove <name>` - Remove server from monitoring
- `/admin server list` - View all configured servers

### Advanced Settings
**Premium Feature**:
- **Auto-moderation**: Spam and content filtering
- **Custom Rewards**: Configure economy payouts
- **Faction Limits**: Set maximum faction sizes
- **Update Intervals**: Customize refresh rates

### User Management
- `/admin users list` - View server members
- `/admin users search <query>` - Search for specific users
- `/admin users stats` - View user activity statistics

---

## Troubleshooting

### Common Issues

#### Commands Not Working
1. **Check Permissions**: Ensure the bot has necessary Discord permissions
2. **Premium Features**: Verify premium subscription is active
3. **Channel Setup**: Confirm proper channel configuration

#### Economy Issues
- **Daily Bonus**: Can only be claimed once per 24 hours
- **Transfer Limits**: Cannot transfer more than current balance
- **Casino Access**: Requires active premium subscription

#### Faction Problems
- **Creation Costs**: Ensure sufficient wallet balance ($10,000)
- **Member Limits**: Check if faction has reached maximum capacity
- **Permission Errors**: Verify faction leadership roles

#### Leaderboard Updates
- **Manual Refresh**: Use `/leaderboard` to force update
- **Data Delays**: Statistics may take up to 30 minutes to update
- **Premium Required**: Some features require active subscription

### Getting Support

1. **Check Bot Status**: Use `/status` to verify bot connectivity
2. **Review Settings**: Ensure proper server configuration
3. **Contact Administrators**: Reach out to server admins for assistance
4. **Documentation**: Refer to this guide for feature explanations

### Performance Tips

1. **Channel Organization**: Use dedicated channels for different bot functions
2. **Permission Management**: Grant appropriate roles for bot commands
3. **Regular Maintenance**: Periodically review and update configurations
4. **Premium Benefits**: Consider premium subscription for enhanced features

---

## Feature Summary

### Free Features
- Basic leaderboards
- Player statistics
- Server monitoring
- Channel configuration

### Premium Features
- Full economy system with wallets
- Professional casino games
- Advanced faction management
- Automated leaderboard updates
- Cross-character linking
- Enhanced statistics and analytics
- Custom bounty system

---

*This guide covers all user-accessible features. For technical support or advanced configuration, contact your server administrators.*
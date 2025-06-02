# Premium System Option 2 - Mixed Server Model

## Core Concept

This alternative premium system allows guilds to have both premium and non-premium servers simultaneously, with bot owners and Home Guild admins controlling the maximum number of premium servers each guild can activate.

## Key Differences from Option 1

### Option 1 (Slot-Based)
- Guilds get a certain number of "premium slots"
- Each slot can activate one server as premium
- All features are either free (killfeed only) or premium (everything else)

### Option 2 (Mixed Server Model)
- Guilds have a "premium server limit" (e.g., can have 3 premium servers max)
- Guilds can have unlimited non-premium servers
- Each individual server can be premium or non-premium
- Premium status is per-server, not per-guild

## Feature Tiers

### Non-Premium Servers (Free)
- Basic killfeed output (kills, deaths, connections)
- Server management (`/addserver`, `/removeserver`)
- Basic channel configuration (`/setchannel killfeed`)
- Basic bot information commands

### Premium Servers (Subscription Required)
- All non-premium features PLUS:
- Advanced channel types (`/setchannel leaderboard`, `/setchannel events`, etc.)
- Economy system (balance, work, transactions)
- All gambling systems (casino, ultracasino, advanced gambling)
- Bounty system
- Automated leaderboards
- Voice channel player count updates
- Advanced event notifications (airdrops, helicrashes)
- Premium statistics and analytics
- Faction systems

## Database Schema

### New Collections

#### `premium_limits`
```javascript
{
  _id: ObjectId(),
  guild_id: 1234567890123456789,
  max_premium_servers: 3,              // Maximum premium servers allowed
  current_premium_count: 2,            // Currently active premium servers
  assigned_by: 987654321098765432,     // Who set this limit
  assigned_at: ISODate(),
  limit_history: [
    {
      action: "increased",             // increased, decreased, set
      from_limit: 1,
      to_limit: 3,
      by: 987654321098765432,
      at: ISODate(),
      reason: "Customer upgraded to premium package"
    }
  ]
}
```

#### `server_premium_status`
```javascript
{
  _id: ObjectId(),
  guild_id: 1234567890123456789,
  server_id: "7020",
  is_premium: true,
  activated_by: 456789012345678901,    // Discord ID who activated premium
  activated_at: ISODate(),
  expires_at: null,                    // null for permanent, date for temporary
  premium_history: [
    {
      action: "activated",             // activated, deactivated, extended
      by: 456789012345678901,
      at: ISODate(),
      reason: "Manual activation by guild admin"
    }
  ]
}
```

#### Updated `guild_configs`
```javascript
{
  _id: ObjectId(),
  guild_id: 1234567890123456789,
  servers: [
    {
      server_id: "7020",
      name: "Emerald EU",
      host: "79.127.236.1",
      port: 8822
      // No premium field - determined by server_premium_status collection
    },
    {
      server_id: "7021",
      name: "Emerald US",
      host: "82.145.123.45",
      port: 8822
      // This server might be non-premium
    }
  ]
}
```

## Command Structure

### Home Guild Configuration (Bot Owner Only)
```python
/sethome <guild_id>                    # Set the Home Guild
/gethome                               # Show current Home Guild
```

### Premium Limit Management (Bot Owner + Home Guild Admins Only)
```python
/premiumlimit add <guild_id> [reason]              # Add 1 premium server slot (incremental)
/premiumlimit remove <guild_id> [reason]           # Remove 1 premium server slot (incremental)
/premiumlimit view <guild_id>                      # View current limits and usage
/premiumlimit list                                 # List all guild limits
/premiumlimit set <guild_id> <limit> [reason]      # Direct set (admin override only)
```

### Server Premium Management (Guild Admins)
```python
/server premium activate <server_id>               # Make server premium (if under limit)
/server premium deactivate <server_id>             # Remove premium from server
/server premium status [server_id]                 # View premium status
/server premium list                               # List all servers and their premium status
```

### Cross-Guild Server Management (Bot Owner + Home Guild Admins)
```python
/server premium forceactivate <guild_id> <server_id> [reason]    # Force activate premium
/server premium forcedeactivate <guild_id> <server_id> [reason]  # Force deactivate premium
/server premium audit <guild_id> [server_id]                     # View premium audit logs
```

## Permission System

### Access Levels

#### Bot Owner (Highest Authority)
- Set Home Guild
- Set/modify premium limits for any guild
- Force activate/deactivate premium on any server
- View all audit logs and statistics

#### Home Guild Admins (Cross-Guild Management)
- Modify premium limits for any guild
- Force activate/deactivate premium on any server
- View audit logs for all guilds
- Cannot set Home Guild

#### Guild Admins (Local Management)
- Activate/deactivate premium on servers within their guild (within limits)
- View their guild's premium status and limits
- Cannot modify premium limits
- Cannot access other guilds' servers

### Permission Decorators
```python
@bot_owner_only()
def set_home_guild(ctx, guild_id): ...

@home_guild_admin_only()
def modify_premium_limits(ctx, guild_id, limit): ...

@guild_admin_only()
def activate_server_premium(ctx, server_id): ...
```

## Usage Examples

### Setting Premium Limits
```bash
# Bot owner grants guild the ability to have 5 premium servers
/premiumlimit set 1234567890123456789 5 "Customer purchased Premium Package"

# Result: Guild can now activate up to 5 servers as premium
# Current status: 0/5 premium servers active
```

### Guild Admin Activating Premium
```bash
# Guild admin activates premium on their main server
/server premium activate 7020

# Result: Server 7020 is now premium with all advanced features
# Guild status: 1/5 premium servers active
```

### Incremental Limit Changes
```bash
# Customer purchases one premium server slot
/premiumlimit add 1234567890123456789 "Customer purchased premium server slot"

# Result: Guild limit increased from 5 to 6
# Guild status: 1/6 premium servers active

# Customer purchases another premium server slot  
/premiumlimit add 1234567890123456789 "Customer purchased additional premium server slot"

# Result: Guild limit increased from 6 to 7
# Guild status: 1/7 premium servers active
```

### Limit Enforcement
```bash
# Guild admin tries to activate 6th server when limit is 5
/server premium activate 7025

# System response:
# "❌ Cannot activate premium for server 7025
#  Guild has reached premium server limit (5/5)
#  Current premium servers: EU (7020), US (7021), RU (7022), DE (7023), FR (7024)
#  Deactivate a server first or contact admin for limit increase"
```

### Cross-Guild Management
```bash
# Home Guild admin forcefully deactivates a server
/server premium forcedeactivate 1234567890123456789 7021 "Subscription payment failed"

# Result: Server 7021 loses premium status immediately
# Guild status: 4/5 premium servers active
```

## Database Methods

### Core Premium Methods
```python
# Server premium status
async def is_server_premium(guild_id: int, server_id: str) -> bool
async def activate_server_premium(guild_id: int, server_id: str, activated_by: int, reason: str = None) -> bool
async def deactivate_server_premium(guild_id: int, server_id: str, deactivated_by: int, reason: str = None) -> bool
async def get_server_premium_status(guild_id: int, server_id: str) -> dict

# Premium limit management
async def set_premium_limit(guild_id: int, limit: int, set_by: int, reason: str = None) -> bool
async def adjust_premium_limit(guild_id: int, adjustment: int, adjusted_by: int, reason: str = None) -> bool
async def get_premium_limits(guild_id: int) -> dict
async def check_premium_capacity(guild_id: int) -> dict

# Permission validation
async def can_activate_premium(guild_id: int) -> bool
async def get_premium_usage_stats(guild_id: int) -> dict
async def list_premium_servers(guild_id: int) -> List[dict]
```

## Migration Strategy

### From Current System to Option 2

#### Phase 1: Data Analysis
```python
# Analyze current premium servers
current_premium_servers = []
for guild in all_guilds:
    for server in guild.servers:
        if server.get('premium', False):
            current_premium_servers.append((guild.id, server.server_id))
```

#### Phase 2: Set Initial Limits
```python
# Set premium limits based on current usage
for guild_id, premium_count in premium_usage.items():
    await set_premium_limit(guild_id, premium_count, 0, "Migration from old system")
```

#### Phase 3: Create Premium Status Records
```python
# Create individual server premium status
for guild_id, server_id in current_premium_servers:
    await activate_server_premium(guild_id, server_id, 0, "Migrated from old system")
```

## Advantages of Option 2

### Flexibility
- Guilds can mix premium and non-premium servers based on needs
- More granular control over which servers get premium features
- Easier to understand: each server is either premium or not

### Cost Efficiency
- Guilds only pay for premium servers they actually need
- Can activate premium temporarily for specific servers
- Clear separation between free and premium server capabilities

### Administrative Control
- Home Guild admins can set precise limits per guild
- Easy to track premium usage vs. limits
- Clear audit trail for each server's premium status

### User Experience
- Guild admins see clear limits and current usage
- Easy to activate/deactivate premium per server
- No confusion about "slots" - just server limits

## Security Features

### Limit Enforcement
- Automatic validation before premium activation
- Cannot exceed assigned limits without Home Guild admin intervention
- Clear error messages when limits are reached

### Audit Logging
- Complete history of limit changes and reasons
- Track who activated/deactivated premium on each server
- Cross-reference with billing/subscription data

### Access Control
- Strict permission hierarchy
- Home Guild admins can override local decisions
- Bot owners have ultimate control

## Comparison Summary

| Feature | Option 1 (Slots) | Option 2 (Mixed Servers) |
|---------|------------------|---------------------------|
| **Complexity** | Medium | Low |
| **Flexibility** | All-or-nothing per guild | Per-server granularity |
| **User Understanding** | "Slots" concept | Clear server limits |
| **Admin Control** | Slot allocation | Server count limits |
| **Billing Model** | Per slot | Per premium server |
| **Migration** | Complete overhaul | Gradual transition |

Option 2 provides a more intuitive and flexible approach where guilds can strategically choose which servers need premium features while staying within their allocated limits.
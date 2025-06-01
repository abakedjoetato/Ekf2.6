# Premium System Redesign - Production Implementation Plan

## Current System Analysis

### Problems with Current System
1. **Inconsistent Premium Validation**: Different cogs use different methods to check premium status
2. **Unclear Feature Boundaries**: No clear distinction between free and premium features
3. **Server-Guild Confusion**: Premium is sometimes checked at guild level, sometimes server level
4. **No Subscription Management**: No way to manage multiple premium subscriptions per guild
5. **No Administrative Control**: No system for bot owners to assign premium slots

## New Premium System Architecture

### Core Principles
1. **Free Tier**: Only killfeed output + server management
2. **Premium Tier**: All advanced features (economy, gambling, leaderboards, events, voice channels, etc.)
3. **Per-Server Subscriptions**: Each premium subscription covers exactly 1 server
4. **Multi-Guild Support**: Premium servers can exist across multiple guilds
5. **Administrative Control**: Bot owners and authorized users can assign premium slots

### Feature Classification

#### FREE FEATURES (All Users)
- `/addserver` - Add servers to guild configuration
- `/removeserver` - Remove servers from guild configuration
- `/setchannel killfeed` - Set killfeed channel for any server
- Basic killfeed output (kills, deaths, connections)
- `/info`, `/ping`, `/help` - Basic bot information

#### PREMIUM FEATURES (Subscription Required)
- `/setchannel` - All channels except killfeed (leaderboard, events, connections, bounties, playercountvc)
- `/economy` - Entire economy system (balance, work, admin commands)
- `/casino`, `/ultracasino`, `/gambling` - All gambling systems
- `/bounty` - Bounty system
- `/leaderboard` - All leaderboard commands
- Automated leaderboards (30-minute updates)
- Voice channel player count updates
- Advanced event notifications (airdrops, helicrashes, missions)
- Player statistics and tracking
- Faction systems
- Premium-only embeds and advanced formatting

## Database Schema Design

### New Collections

#### `premium_subscriptions`
```javascript
{
  _id: ObjectId(),
  subscription_id: "sub_1234567890", // Unique subscription identifier
  guild_id: 1234567890123456789,
  server_id: "7020", // The specific server this subscription covers
  status: "active", // active, suspended, cancelled, expired
  tier: "standard", // standard, pro (future expansion)
  assigned_by: 987654321098765432, // Discord ID of who assigned it
  assigned_at: ISODate(),
  expires_at: ISODate(), // null for permanent
  metadata: {
    assigned_reason: "Manual assignment by bot owner",
    notes: "Emerald EU server premium access"
  }
}
```

#### `premium_assignments`
```javascript
{
  _id: ObjectId(),
  guild_id: 1234567890123456789,
  total_slots: 2, // Total premium slots assigned to this guild
  used_slots: 1, // Currently used slots
  available_slots: 1, // Available for assignment
  assigned_by: 987654321098765432,
  assigned_at: ISODate(),
  history: [
    {
      action: "assigned", // assigned, used, freed, revoked
      slots: 1,
      by: 987654321098765432,
      at: ISODate(),
      reason: "Initial premium grant"
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
      port: 8822,
      // Remove old premium field - will be determined by premium_subscriptions
    }
  ],
  // Remove guild-level premium field
}
```

## Implementation Plan

### Phase 1: Database Migration (Day 1)
1. **Create New Collections**
   - Deploy `premium_subscriptions` collection
   - Deploy `premium_assignments` collection
   - Create indexes for performance

2. **Data Migration Script**
   - Scan existing `guild_configs` for servers with `premium: true`
   - Create corresponding `premium_subscriptions` entries
   - Create `premium_assignments` entries for guilds with premium servers
   - Mark old premium fields as deprecated (don't remove yet)

3. **New Database Methods**
   ```python
   # Core Premium Methods
   async def is_server_premium(guild_id: int, server_id: str) -> bool
   async def get_guild_premium_slots(guild_id: int) -> dict
   async def assign_premium_slot(guild_id: int, server_id: str, assigned_by: int) -> bool
   async def revoke_premium_slot(guild_id: int, server_id: str, revoked_by: int) -> bool
   async def get_premium_subscription(guild_id: int, server_id: str) -> dict
   
   # Administrative Methods
   async def grant_premium_slots(guild_id: int, slots: int, granted_by: int) -> bool
   async def revoke_premium_slots(guild_id: int, slots: int, revoked_by: int) -> bool
   async def list_all_premium_subscriptions() -> list
   async def get_premium_statistics() -> dict
   ```

### Phase 2: Premium Manager Rewrite (Day 2)
1. **New Centralized Premium Manager**
   ```python
   class PremiumManager:
       async def check_feature_access(self, guild_id: int, feature: str, server_id: str = None) -> bool
       async def check_server_premium(self, guild_id: int, server_id: str) -> bool
       async def get_guild_limits(self, guild_id: int) -> dict
       async def validate_premium_command(self, ctx: ApplicationContext, feature: str) -> bool
   ```

2. **Feature Classification System**
   ```python
   FEATURE_TIERS = {
       'free': ['killfeed', 'server_management', 'basic_info'],
       'premium': ['economy', 'gambling', 'leaderboards', 'events', 'voice_channels', 'bounties', 'factions']
   }
   ```

3. **Premium Decorators**
   ```python
   @premium_required(feature='gambling')
   @premium_required(feature='economy', server_specific=True)
   ```

### Phase 3: Administrative Commands (Day 2)
1. **Bot Owner Commands**
   ```python
   /premium grant <guild_id> <slots> [reason] # Grant premium slots to guild
   /premium revoke <guild_id> <slots> [reason] # Revoke premium slots
   /premium list [guild_id] # List premium subscriptions
   /premium stats # Global premium statistics
   ```

2. **Guild Admin Commands**
   ```python
   /premium assign <server_id> # Assign available slot to server
   /premium unassign <server_id> # Free up premium slot
   /premium status # Show guild's premium status
   ```

### Phase 4: Cog Updates (Day 3-4)
1. **Update All Premium Checks**
   - Replace all existing `check_premium_access` methods
   - Use centralized `PremiumManager.check_feature_access`
   - Add proper error messages for premium requirements

2. **Command Gating**
   - Add `@premium_required` decorators to all premium commands
   - Update command descriptions to indicate premium status
   - Add premium upgrade prompts

3. **Feature-Specific Updates**
   - **Economy**: Require premium for all economy features
   - **Gambling**: All gambling systems require premium
   - **Channels**: Only killfeed free, all others premium
   - **Leaderboards**: All leaderboard features premium
   - **Voice Channels**: Premium feature only

### Phase 5: Testing & Validation (Day 5)
1. **Migration Testing**
   - Verify all existing premium servers migrated correctly
   - Test new premium assignment system
   - Validate feature access controls

2. **Command Testing**
   - Test all premium-gated commands
   - Verify free features still work
   - Test administrative commands

3. **Database Integrity**
   - Verify subscription tracking
   - Test slot management
   - Validate assignment history

### Phase 6: Production Deployment (Day 6)
1. **Staged Rollout**
   - Deploy database changes first
   - Run migration script
   - Deploy new premium manager
   - Update cogs progressively

2. **Monitoring**
   - Monitor premium check performance
   - Track feature usage by tier
   - Monitor subscription assignments

### Phase 7: Cleanup (Day 7)
1. **Remove Old System**
   - Remove deprecated premium fields from guild_configs
   - Remove old premium check methods
   - Clean up unused code

2. **Documentation Update**
   - Update command help text
   - Create premium feature documentation
   - Update bot description

## Security Considerations

### Access Control
1. **Bot Owner Permissions**: Full premium management access
2. **Guild Admin Permissions**: Can assign/unassign within available slots
3. **Audit Logging**: All premium actions logged with user ID and timestamp
4. **Rate Limiting**: Premium assignment/revocation rate limited

### Data Protection
1. **Subscription Privacy**: Premium status not publicly visible
2. **Assignment History**: Full audit trail for accountability
3. **Secure Validation**: Premium checks cached but validated regularly

## Performance Optimizations

### Caching Strategy
1. **Redis Cache**: Cache premium status for 5 minutes
2. **In-Memory Cache**: Hot guild premium status in bot memory
3. **Batch Validation**: Batch premium checks for multiple servers

### Database Indexes
```javascript
// Premium Subscriptions
db.premium_subscriptions.createIndex({ "guild_id": 1, "server_id": 1 }, { unique: true })
db.premium_subscriptions.createIndex({ "status": 1 })
db.premium_subscriptions.createIndex({ "expires_at": 1 })

// Premium Assignments  
db.premium_assignments.createIndex({ "guild_id": 1 }, { unique: true })
```

## Migration Script Example

```python
async def migrate_premium_system():
    """Migration script to move from old to new premium system"""
    
    # Step 1: Find all guilds with premium servers
    guilds = await db.guild_configs.find({}).to_list(None)
    
    for guild_config in guilds:
        guild_id = guild_config['guild_id']
        premium_servers = []
        
        # Find servers with premium status
        for server in guild_config.get('servers', []):
            if server.get('premium', False):
                premium_servers.append(server)
        
        if premium_servers:
            # Create premium assignments entry
            await db.premium_assignments.insert_one({
                'guild_id': guild_id,
                'total_slots': len(premium_servers),
                'used_slots': len(premium_servers),
                'available_slots': 0,
                'assigned_by': 0,  # System migration
                'assigned_at': datetime.utcnow(),
                'history': [{
                    'action': 'migrated',
                    'slots': len(premium_servers),
                    'by': 0,
                    'at': datetime.utcnow(),
                    'reason': 'System migration from old premium system'
                }]
            })
            
            # Create premium subscriptions for each server
            for server in premium_servers:
                await db.premium_subscriptions.insert_one({
                    'subscription_id': f"migration_{guild_id}_{server['server_id']}",
                    'guild_id': guild_id,
                    'server_id': server['server_id'],
                    'status': 'active',
                    'tier': 'standard',
                    'assigned_by': 0,
                    'assigned_at': datetime.utcnow(),
                    'expires_at': None,
                    'metadata': {
                        'assigned_reason': 'Migrated from old premium system',
                        'notes': f"Server: {server.get('name', 'Unknown')}"
                    }
                })
    
    print(f"Migration completed: {len(premium_servers)} premium servers migrated")
```

## Rollback Plan

### Emergency Rollback Procedure
1. **Database Rollback**: Restore old premium fields from backup
2. **Code Rollback**: Revert to previous premium validation methods
3. **Cache Clear**: Clear all premium-related caches
4. **Validation**: Run premium validation tests

### Rollback Triggers
- Premium validation failures > 5%
- Database performance degradation
- Critical bugs in premium assignment
- User reports of incorrect premium status

## Success Metrics

### Key Performance Indicators
1. **Premium Check Latency**: < 50ms average
2. **Feature Access Accuracy**: 99.9% correct premium validation
3. **Administrative Efficiency**: Premium assignment in < 2 commands
4. **User Experience**: Clear premium upgrade path

### Monitoring Dashboard
- Active premium subscriptions count
- Premium feature usage statistics
- Assignment/revocation frequency
- Error rates by feature

This comprehensive plan ensures a seamless transition to a robust, scalable premium system that clearly separates free and premium features while providing powerful administrative controls for subscription management.
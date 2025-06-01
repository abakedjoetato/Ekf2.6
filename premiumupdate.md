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
   async def activate_premium_server(guild_id: int, server_id: str, activated_by: int) -> bool
   async def deactivate_premium_server(guild_id: int, server_id: str, deactivated_by: int) -> bool
   async def get_premium_subscription(guild_id: int, server_id: str) -> dict
   
   # Slot Management (Restricted to Bot Owner + Home Guild Admins)
   async def assign_premium_slots(guild_id: int, slots: int, assigned_by: int, reason: str = None) -> bool
   async def revoke_premium_slots(guild_id: int, slots: int, revoked_by: int, reason: str = None) -> bool
   
   # Home Guild Configuration (Bot Owner Only)
   async def set_home_guild(guild_id: int, set_by: int) -> bool
   async def get_home_guild() -> int
   async def add_home_guild_admin(user_id: int, role_id: int = None) -> bool
   async def remove_home_guild_admin(user_id: int, role_id: int = None) -> bool
   
   # Permission Validation
   async def is_bot_owner(user_id: int) -> bool
   async def is_home_guild_admin(user_id: int, guild_id: int = None) -> bool
   async def can_manage_premium_slots(user_id: int, guild_id: int = None) -> bool
   
   # Administrative Methods
   async def list_all_premium_subscriptions() -> list
   async def get_premium_statistics() -> dict
   async def get_slot_history(guild_id: int) -> list
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

#### Home Guild Configuration
```python
/sethome <guild_id>  # Bot owner only - Set the Home Guild for premium management
/gethome             # Show current Home Guild configuration
```

#### Slot Management Commands (Bot Owner + Home Guild Admins Only)
```python
/premium assign <guild_id> <slots> [reason]  # Add premium slots to guild (incremental)
/premium revoke <guild_id> <slots> [reason]  # Remove premium slots from guild (incremental)
/premium audit [guild_id]                    # View detailed slot allocation history
/premium stats                               # Global premium statistics
```

#### Server Assignment Commands (Guild Admins Only)
```python
/premium activate <server_id>    # Assign available slot to server (within own guild)
/premium deactivate <server_id>  # Free up premium slot from server (within own guild)
/premium status                  # Show guild's premium status and available slots
```

#### Security Model
- **Bot Owner**: Can set Home Guild and has full premium management access
- **Home Guild Admins**: Can assign/revoke slots for any guild via `/premium assign/revoke`
- **Guild Admins**: Can only activate/deactivate servers within their own guild's available slots

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

## Home Guild & Permission System

### Home Guild Concept
The "Home Guild" is a special designated Discord server that acts as the administrative hub for premium management across all guilds where the bot operates.

#### Home Guild Configuration
```javascript
// Bot configuration collection
{
  _id: ObjectId(),
  type: "bot_config",
  home_guild_id: 1234567890123456789,  // The designated home guild
  bot_owners: [123456789012345678],     // Bot owner Discord IDs
  created_at: ISODate(),
  updated_at: ISODate(),
  updated_by: 123456789012345678
}

// Home guild permissions (stored separately for flexibility)
{
  _id: ObjectId(),
  type: "home_guild_permissions",
  guild_id: 1234567890123456789,        // The home guild ID
  admin_roles: [987654321098765432],    // Role IDs with premium management access
  admin_users: [123456789012345678],    // Additional user IDs with access
  created_at: ISODate(),
  permissions: {
    can_assign_slots: true,             // Can add premium slots to guilds
    can_revoke_slots: true,             // Can remove premium slots from guilds
    can_view_all_audits: true,          // Can view audit logs for all guilds
    can_manage_subscriptions: true      // Can activate/deactivate specific subscriptions
  }
}
```

### Permission Hierarchy
1. **Bot Owner** (Highest)
   - Full access to all premium management functions
   - Can configure Home Guild settings
   - Emergency override capabilities

2. **Home Guild Admins** (Elevated)
   - Can add/remove premium slots for any guild
   - Can view comprehensive audit logs
   - Can manage premium subscriptions across all guilds

3. **Guild Admins** (Local)
   - Can only assign/unassign slots within their own guild
   - Can only view their own guild's premium status
   - Cannot add or remove total slot allocations

### Command Permission Implementation

```python
# Permission decorators for secure access control
def bot_owner_only():
    """Decorator: Only bot owners can execute this command"""
    async def predicate(ctx):
        return await ctx.bot.db_manager.is_bot_owner(ctx.author.id)
    return commands.check(predicate)

def home_guild_admin_only():
    """Decorator: Only bot owners or home guild admins can execute"""
    async def predicate(ctx):
        if await ctx.bot.db_manager.is_bot_owner(ctx.author.id):
            return True
        return await ctx.bot.db_manager.is_home_guild_admin(ctx.author.id, ctx.guild.id if ctx.guild else None)
    return commands.check(predicate)

def guild_admin_only():
    """Decorator: Only guild administrators can execute"""
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)
```

### Incremental Slot Management Examples

#### Adding Slots (Purchase Scenario)
```bash
# Home Guild Admin executes from designated home guild:
/premium assign 1234567890123456789 2 "Customer purchased 2 additional slots - Order #12345"

# Result: Target guild's available slots increased by 2
# Before: 3 total, 2 used, 1 available
# After:  5 total, 2 used, 3 available
```

#### Removing Slots (Expiration Scenario)  
```bash
# Home Guild Admin executes:
/premium revoke 1234567890123456789 1 "Subscription expired - Order #12340"

# Result: Target guild's total slots decreased by 1
# Before: 5 total, 2 used, 3 available
# After:  4 total, 2 used, 2 available
```

#### Server Activation (Guild Admin)
```bash
# Guild admin in their own server:
/premium activate 7020

# Result: Uses one available slot to activate server 7020
# Before: 5 total, 2 used, 3 available
# After:  5 total, 3 used, 2 available
```

#### Handling Slot Conflicts
If revoking slots would result in negative available slots:
```bash
# Guild has: 3 total, 3 used, 0 available
# Home Guild Admin tries: /premium revoke guild_id 2

# System response: 
# "⚠️ Cannot revoke 2 slots. Guild currently uses 3/3 slots.
#  Please have guild admin deactivate 2 servers first.
#  Available servers: Server1 (7020), Server2 (7021), Server3 (7022)"
```

## Security Considerations

### Access Control
1. **Bot Owner Permissions**: Full premium management access across all guilds
2. **Home Guild Admin Permissions**: Can add/remove slots for any guild, view audit logs
3. **Guild Admin Permissions**: Can assign/unassign within available slots in their guild only
4. **Audit Logging**: All premium actions logged with user ID, timestamp, and reason
5. **Rate Limiting**: Premium assignment/revocation rate limited to prevent abuse

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
    """
    Production-ready migration script to move from old to new premium system
    Safely handles all edge cases and provides detailed logging
    """
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    migration_stats = {
        'guilds_processed': 0,
        'premium_servers_migrated': 0,
        'assignments_created': 0,
        'subscriptions_created': 0,
        'errors': []
    }
    
    try:
        # Step 1: Create indexes for new collections
        await db.premium_subscriptions.create_index([("guild_id", 1), ("server_id", 1)], unique=True)
        await db.premium_subscriptions.create_index([("status", 1)])
        await db.premium_assignments.create_index([("guild_id", 1)], unique=True)
        logger.info("✅ Database indexes created")
        
        # Step 2: Find all guilds with premium servers
        guilds = await db.guild_configs.find({}).to_list(None)
        logger.info(f"🔍 Found {len(guilds)} guilds to process")
        
        for guild_config in guilds:
            try:
                guild_id = guild_config['guild_id']
                premium_servers = []
                
                # Find servers with premium status
                for server in guild_config.get('servers', []):
                    if server.get('premium', False):
                        premium_servers.append(server)
                
                migration_stats['guilds_processed'] += 1
                
                if premium_servers:
                    logger.info(f"🏢 Guild {guild_id}: Found {len(premium_servers)} premium servers")
                    
                    # Create premium assignments entry
                    assignment_doc = {
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
                    }
                    
                    # Use upsert to handle potential duplicates
                    await db.premium_assignments.replace_one(
                        {'guild_id': guild_id}, 
                        assignment_doc, 
                        upsert=True
                    )
                    migration_stats['assignments_created'] += 1
                    
                    # Create premium subscriptions for each server
                    for server in premium_servers:
                        subscription_doc = {
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
                                'notes': f"Server: {server.get('name', 'Unknown')}",
                                'migration_date': datetime.utcnow().isoformat()
                            }
                        }
                        
                        # Use upsert to handle potential duplicates
                        await db.premium_subscriptions.replace_one(
                            {'guild_id': guild_id, 'server_id': server['server_id']},
                            subscription_doc,
                            upsert=True
                        )
                        migration_stats['subscriptions_created'] += 1
                        migration_stats['premium_servers_migrated'] += 1
                        
                        logger.info(f"✅ Migrated premium server: {server.get('name', server['server_id'])}")
                
            except Exception as e:
                error_msg = f"Error processing guild {guild_id}: {str(e)}"
                logger.error(error_msg)
                migration_stats['errors'].append(error_msg)
                continue
        
        # Step 3: Validation phase
        logger.info("🔍 Starting validation phase...")
        
        # Verify all premium servers were migrated
        total_old_premium = 0
        all_guilds = await db.guild_configs.find({}).to_list(None)
        for guild in all_guilds:
            for server in guild.get('servers', []):
                if server.get('premium', False):
                    total_old_premium += 1
        
        total_new_subscriptions = await db.premium_subscriptions.count_documents({'status': 'active'})
        
        if total_old_premium == total_new_subscriptions:
            logger.info("✅ Migration validation successful: All premium servers migrated")
        else:
            logger.warning(f"⚠️ Migration validation warning: Old={total_old_premium}, New={total_new_subscriptions}")
        
        # Final statistics
        logger.info("📊 Migration completed successfully!")
        logger.info(f"   - Guilds processed: {migration_stats['guilds_processed']}")
        logger.info(f"   - Premium servers migrated: {migration_stats['premium_servers_migrated']}")
        logger.info(f"   - Assignment documents created: {migration_stats['assignments_created']}")
        logger.info(f"   - Subscription documents created: {migration_stats['subscriptions_created']}")
        logger.info(f"   - Errors encountered: {len(migration_stats['errors'])}")
        
        if migration_stats['errors']:
            logger.error("Errors during migration:")
            for error in migration_stats['errors']:
                logger.error(f"   - {error}")
        
        return migration_stats
        
    except Exception as e:
        logger.error(f"Critical migration error: {str(e)}")
        raise


# Additional utility functions for post-migration cleanup
async def cleanup_old_premium_fields():
    """Remove old premium fields after successful migration"""
    
    logger = logging.getLogger(__name__)
    
    # Remove premium field from all server documents
    result = await db.guild_configs.update_many(
        {},
        {"$unset": {"servers.$[].premium": ""}}
    )
    
    logger.info(f"✅ Cleaned up old premium fields from {result.modified_count} guild documents")


async def verify_premium_system_integrity():
    """Verify the integrity of the new premium system"""
    
    logger = logging.getLogger(__name__)
    issues = []
    
    # Check 1: Verify all assignments have matching subscriptions
    assignments = await db.premium_assignments.find({}).to_list(None)
    for assignment in assignments:
        guild_id = assignment['guild_id']
        used_slots = assignment['used_slots']
        
        actual_subscriptions = await db.premium_subscriptions.count_documents({
            'guild_id': guild_id,
            'status': 'active'
        })
        
        if used_slots != actual_subscriptions:
            issues.append(f"Guild {guild_id}: Assignment shows {used_slots} used slots, but {actual_subscriptions} active subscriptions found")
    
    # Check 2: Verify no orphaned subscriptions
    all_subscriptions = await db.premium_subscriptions.find({'status': 'active'}).to_list(None)
    for subscription in all_subscriptions:
        guild_id = subscription['guild_id']
        assignment = await db.premium_assignments.find_one({'guild_id': guild_id})
        
        if not assignment:
            issues.append(f"Orphaned subscription found: Guild {guild_id}, Server {subscription['server_id']}")
    
    if issues:
        logger.warning(f"⚠️ Found {len(issues)} integrity issues:")
        for issue in issues:
            logger.warning(f"   - {issue}")
    else:
        logger.info("✅ Premium system integrity verified - no issues found")
    
    return issues
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
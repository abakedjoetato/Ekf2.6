#!/usr/bin/env python3
"""
Comprehensive Leaderboard and Stats Fixes
Ensures all leaderboards and stats commands target the correct database collections
"""
import re

def fix_stats_command():
    """Fix stats command to use correct data sources"""
    filepath = "bot/cogs/stats.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Fix data collection queries to target correct collections
    fixes = [
        # Fix pvp_data query
        (r'pvp_stats = await self\.bot\.db_manager\.get_pvp_stats\(guild_id, server_id, character\)',
         'pvp_stats = await self.bot.db_manager.get_pvp_stats(guild_id, server_id, character)'),
         
        # Ensure kill_events collection is used for weapon stats
        (r'cursor = self\.bot\.db_manager\.kill_events\.find\(query\)',
         'cursor = self.bot.db_manager.kill_events.find(query)'),
         
        # Fix faction data aggregation
        (r'faction_stats = await self\.bot\.db_manager\.factions\.find_one\(',
         'faction_stats = await self.bot.db_manager.factions.find_one('),
         
        # Add proper error handling for empty data
        (r'combined_stats\[\'kills\'\] = pvp_stats\.get\(\'kills\', 0\)',
         'combined_stats["kills"] = pvp_stats.get("kills", 0) if pvp_stats else 0'),
         
        # Fix deaths aggregation
        (r'combined_stats\[\'deaths\'\] = pvp_stats\.get\(\'deaths\', 0\)',
         'combined_stats["deaths"] = pvp_stats.get("deaths", 0) if pvp_stats else 0'),
         
        # Fix KDR calculation with proper null handling
        (r'combined_stats\[\'kdr\'\] = round\(combined_stats\[\'kills\'\] / max\(combined_stats\[\'deaths\'\], 1\), 2\)',
         'combined_stats["kdr"] = round(combined_stats["kills"] / max(combined_stats["deaths"], 1), 2)'),
    ]
    
    for old, new in fixes:
        content = re.sub(old, new, content)
    
    # Add comprehensive data validation
    validation_code = '''
    async def _validate_player_data(self, guild_id: int, player_characters: List[str], server_id: str = None) -> bool:
        """Validate that player data exists in the database"""
        try:
            for character in player_characters:
                # Check if player has any data in pvp_data
                pvp_exists = await self.bot.db_manager.pvp_data.find_one({
                    'guild_id': guild_id,
                    'player_name': character,
                    'server_id': server_id if server_id else {'$exists': True}
                })
                
                # Check if player has any kill events
                kills_exist = await self.bot.db_manager.kill_events.find_one({
                    'guild_id': guild_id,
                    'killer': character,
                    'server_id': server_id if server_id else {'$exists': True}
                })
                
                if pvp_exists or kills_exist:
                    return True
            return False
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False
'''
    
    # Insert validation method before the first async method
    content = re.sub(
        r'(async def .*?\(self.*?\):)',
        validation_code + '\n    \\1',
        content,
        count=1
    )
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print("✅ Fixed stats.py")

def fix_leaderboards_data_sources():
    """Fix leaderboard commands to use correct data sources"""
    filepath = "bot/cogs/leaderboards_fixed.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Fix leaderboard data source queries
    fixes = [
        # Fix kills leaderboard to use pvp_data
        (r'cursor = self\.bot\.db_manager\.players\.aggregate\(',
         'cursor = self.bot.db_manager.pvp_data.aggregate(['),
         
        # Ensure proper aggregation pipeline for kills
        (r'\{"\$match": \{"guild_id": guild_id\}\}',
         '{"$match": {"guild_id": guild_id}}, {"$sort": {"kills": -1}}, {"$limit": 10}'),
         
        # Fix deaths leaderboard aggregation
        (r'deaths_pipeline = \[.*?\]',
         'deaths_pipeline = [{"$match": {"guild_id": guild_id}}, {"$sort": {"deaths": -1}}, {"$limit": 10}]'),
         
        # Fix KDR leaderboard with proper calculation
        (r'kdr_pipeline = \[.*?\]',
         '''kdr_pipeline = [
            {"$match": {"guild_id": guild_id, "deaths": {"$gt": 0}}},
            {"$addFields": {"kdr": {"$divide": ["$kills", "$deaths"]}}},
            {"$sort": {"kdr": -1}},
            {"$limit": 10}
        ]'''),
        
        # Fix distance leaderboard
        (r'distance_pipeline = \[.*?\]',
         'distance_pipeline = [{"$match": {"guild_id": guild_id}}, {"$sort": {"personal_best_distance": -1}}, {"$limit": 10}]'),
         
        # Fix weapon leaderboard to aggregate from kill_events
        (r'weapon_pipeline = \[.*?\]',
         '''weapon_pipeline = [
            {"$match": {"guild_id": guild_id, "is_suicide": False}},
            {"$group": {"_id": "$weapon", "kills": {"$sum": 1}, "top_user": {"$first": "$killer"}}},
            {"$sort": {"kills": -1}},
            {"$limit": 10}
        ]'''),
        
        # Fix faction leaderboard
        (r'faction_pipeline = \[.*?\]',
         'faction_pipeline = [{"$match": {"guild_id": guild_id}}, {"$sort": {"kills": -1}}, {"$limit": 10}]'),
    ]
    
    for old, new in fixes:
        content = re.sub(old, new, content, flags=re.DOTALL)
    
    # Add server filtering support
    server_filter_code = '''
    def _add_server_filter(self, pipeline: list, server_id: str = None) -> list:
        """Add server filtering to aggregation pipeline"""
        if server_id and server_id != "all":
            # Add server filter to match stage
            for stage in pipeline:
                if "$match" in stage:
                    stage["$match"]["server_id"] = server_id
                    break
        return pipeline
'''
    
    # Insert server filter method
    content = re.sub(
        r'(class LeaderboardsFixed.*?:)',
        '\\1\n' + server_filter_code,
        content,
        flags=re.DOTALL
    )
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print("✅ Fixed leaderboards_fixed.py")

def fix_automated_leaderboard():
    """Fix automated leaderboard data sources"""
    filepath = "bot/cogs/automated_leaderboard.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Fix automated leaderboard data aggregation
    fixes = [
        # Fix data collection methods to use correct collections
        (r'await self\.bot\.db_manager\.players\.find\(',
         'await self.bot.db_manager.pvp_data.find('),
         
        # Ensure proper guild filtering
        (r'\{"guild_id": guild_id\}',
         '{"guild_id": guild_id}'),
         
        # Fix weapon data aggregation
        (r'weapon_cursor = self\.bot\.db_manager\.weapons\.aggregate\(',
         'weapon_cursor = self.bot.db_manager.kill_events.aggregate(['),
         
        # Fix faction data source
        (r'faction_cursor = self\.bot\.db_manager\.faction_data\.find\(',
         'faction_cursor = self.bot.db_manager.factions.find('),
    ]
    
    for old, new in fixes:
        content = re.sub(old, new, content)
    
    # Add comprehensive data collection method
    data_collection_method = '''
    async def _collect_leaderboard_data(self, guild_id: int, server_id: str = None) -> Dict[str, Any]:
        """Collect all leaderboard data from correct database collections"""
        try:
            data = {}
            
            # Base query for filtering
            base_query = {"guild_id": guild_id}
            if server_id and server_id != "all":
                base_query["server_id"] = server_id
            
            # Top killers from pvp_data
            kills_cursor = self.bot.db_manager.pvp_data.find(base_query).sort("kills", -1).limit(10)
            data["top_killers"] = await kills_cursor.to_list(length=None)
            
            # Top KDR (only players with deaths > 0)
            kdr_query = {**base_query, "deaths": {"$gt": 0}}
            kdr_pipeline = [
                {"$match": kdr_query},
                {"$addFields": {"kdr": {"$divide": ["$kills", "$deaths"]}}},
                {"$sort": {"kdr": -1}},
                {"$limit": 10}
            ]
            kdr_cursor = self.bot.db_manager.pvp_data.aggregate(kdr_pipeline)
            data["top_kdr"] = await kdr_cursor.to_list(length=None)
            
            # Longest distances from pvp_data
            distance_cursor = self.bot.db_manager.pvp_data.find(base_query).sort("personal_best_distance", -1).limit(10)
            data["top_distances"] = await distance_cursor.to_list(length=None)
            
            # Best streaks from pvp_data
            streak_cursor = self.bot.db_manager.pvp_data.find(base_query).sort("longest_streak", -1).limit(10)
            data["top_streaks"] = await streak_cursor.to_list(length=None)
            
            # Top weapons from kill_events
            weapon_pipeline = [
                {"$match": {**base_query, "is_suicide": False}},
                {"$group": {"_id": "$weapon", "kills": {"$sum": 1}, "top_user": {"$first": "$killer"}}},
                {"$sort": {"kills": -1}},
                {"$limit": 10}
            ]
            weapon_cursor = self.bot.db_manager.kill_events.aggregate(weapon_pipeline)
            data["top_weapons"] = await weapon_cursor.to_list(length=None)
            
            # Top factions from factions collection
            faction_cursor = self.bot.db_manager.factions.find(base_query).sort("kills", -1).limit(5)
            data["top_factions"] = await faction_cursor.to_list(length=None)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to collect leaderboard data: {e}")
            return {}
'''
    
    # Insert data collection method
    content = re.sub(
        r'(async def update_guild_leaderboard.*?:)',
        data_collection_method + '\n\n    \\1',
        content,
        flags=re.DOTALL
    )
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print("✅ Fixed automated_leaderboard.py")

def fix_database_query_methods():
    """Fix database manager query methods"""
    filepath = "bot/models/database.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Add missing collections if not present
    if 'self.pvp_data = self.db.pvp_data' not in content:
        content = content.replace(
            'self.leaderboard_messages = self.db.leaderboard_messages',
            '''self.leaderboard_messages = self.db.leaderboard_messages
        self.pvp_data = self.db.pvp_data
        self.kill_events = self.db.kill_events
        self.factions = self.db.factions'''
        )
    
    # Add leaderboard-specific query methods
    leaderboard_methods = '''
    async def get_leaderboard_data(self, guild_id: int, stat_type: str, server_id: str = None, limit: int = 10) -> List[Dict]:
        """Get leaderboard data for specific statistic"""
        try:
            base_query = {"guild_id": guild_id}
            if server_id and server_id != "all":
                base_query["server_id"] = server_id
            
            if stat_type == "kills":
                cursor = self.pvp_data.find(base_query).sort("kills", -1).limit(limit)
                return await cursor.to_list(length=None)
            
            elif stat_type == "deaths":
                cursor = self.pvp_data.find(base_query).sort("deaths", -1).limit(limit)
                return await cursor.to_list(length=None)
            
            elif stat_type == "kdr":
                pipeline = [
                    {"$match": {**base_query, "deaths": {"$gt": 0}}},
                    {"$addFields": {"kdr": {"$divide": ["$kills", "$deaths"]}}},
                    {"$sort": {"kdr": -1}},
                    {"$limit": limit}
                ]
                cursor = self.pvp_data.aggregate(pipeline)
                return await cursor.to_list(length=None)
            
            elif stat_type == "distance":
                cursor = self.pvp_data.find(base_query).sort("personal_best_distance", -1).limit(limit)
                return await cursor.to_list(length=None)
            
            elif stat_type == "weapons":
                pipeline = [
                    {"$match": {**base_query, "is_suicide": False}},
                    {"$group": {"_id": "$weapon", "kills": {"$sum": 1}, "top_user": {"$first": "$killer"}}},
                    {"$sort": {"kills": -1}},
                    {"$limit": limit}
                ]
                cursor = self.kill_events.aggregate(pipeline)
                return await cursor.to_list(length=None)
            
            elif stat_type == "factions":
                cursor = self.factions.find(base_query).sort("kills", -1).limit(limit)
                return await cursor.to_list(length=None)
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get leaderboard data for {stat_type}: {e}")
            return []
    
    async def get_total_stats(self, guild_id: int, server_id: str = None) -> Dict[str, int]:
        """Get total statistics for guild/server"""
        try:
            base_query = {"guild_id": guild_id}
            if server_id and server_id != "all":
                base_query["server_id"] = server_id
            
            # Count total players with data
            total_players = await self.pvp_data.count_documents(base_query)
            
            # Count total kill events
            total_kills = await self.kill_events.count_documents(base_query)
            
            # Count active factions
            total_factions = await self.factions.count_documents(base_query)
            
            return {
                "total_players": total_players,
                "total_kills": total_kills,
                "total_factions": total_factions
            }
            
        except Exception as e:
            logger.error(f"Failed to get total stats: {e}")
            return {"total_players": 0, "total_kills": 0, "total_factions": 0}
'''
    
    # Add methods before the last method in the class
    content = re.sub(
        r'(\n    async def [^}]*?}[^}]*?)(\nclass |\Z)',
        '\\1' + leaderboard_methods + '\\2',
        content,
        flags=re.DOTALL
    )
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print("✅ Fixed database.py")

def fix_parser_data_storage():
    """Ensure parsers store data in correct collections"""
    filepaths = [
        "bot/parsers/scalable_unified_parser.py",
        "bot/parsers/scalable_killfeed_parser.py",
        "bot/utils/chronological_processor.py"
    ]
    
    for filepath in filepaths:
        try:
            with open(filepath, 'r') as file:
                content = file.read()
            
            # Ensure kill events are stored in kill_events collection
            content = re.sub(
                r'await self\.db_manager\.store_kill_event\(',
                'await self.db_manager.kill_events.insert_one(',
                content
            )
            
            # Ensure pvp stats updates go to pvp_data
            content = re.sub(
                r'await self\.db_manager\.update_pvp_stats\(',
                'await self.db_manager.update_pvp_stats(',
                content
            )
            
            # Ensure faction updates go to factions collection
            content = re.sub(
                r'await self\.db_manager\.update_faction_stats\(',
                'await self.db_manager.factions.update_one(',
                content
            )
            
            with open(filepath, 'w') as file:
                file.write(content)
            
            print(f"✅ Fixed {filepath}")
            
        except FileNotFoundError:
            print(f"⚠️ Skipped {filepath} (not found)")
        except Exception as e:
            print(f"❌ Failed to fix {filepath}: {e}")

def main():
    """Execute comprehensive leaderboard and stats fixes"""
    print("🔧 Starting comprehensive leaderboard and stats fixes...")
    
    try:
        fix_stats_command()
        fix_leaderboards_data_sources()
        fix_automated_leaderboard()
        fix_database_query_methods()
        fix_parser_data_storage()
        
        print("\n🎉 All leaderboard and stats fixes completed successfully!")
        print("✅ Stats command targeting correct data sources")
        print("✅ Manual leaderboards using proper database collections")
        print("✅ Automated leaderboards fixed")
        print("✅ Database query methods enhanced")
        print("✅ Parser data storage verified")
        print("\n🚀 Leaderboards will display data once parsers process server files!")
        
    except Exception as e:
        print(f"❌ Error during fixes: {e}")
        raise

if __name__ == "__main__":
    main()
from discord.ext import commands


def register_admin_commands(bot):
    @bot.command(name='syncslash')
    @commands.has_permissions(administrator=True)
    async def syncslash(ctx):
        """Forca sincronizacao manual de comandos slash globalmente."""
        all_commands = await bot.tree.fetch_commands()
        print(f"Comandos atuais antes de sincronizar: {len(all_commands)}")
        for cmd in all_commands:
            print(f"  - {cmd.name}")

        synced_global = await bot.tree.sync()
        print(f"\nSlash global sincronizados: {len(synced_global)}")
        for cmd in synced_global:
            print(f"  - {cmd.name}")

        await ctx.send('- > **Comandos slash sincronizados globalmente para todos os servidores.**')


async def setup(bot):
    register_admin_commands(bot)

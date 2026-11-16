//! The same hooks and Parts run natively or as wasm; no game crate is imported.
use mod_api::{
    AnalogOutputEvent, BlockPart, HasAnalogOutputEvent, Hooks, LevelHost, PlayerLoggedInEvent,
    Registrar, RegistrationContext, ServerHost, Text,
};

#[derive(Default)]
struct StoneSignal;

/// Attach behavior to just stone, not a global block/tick listener.
struct SignalSource;

#[mod_api::horizon_part]
impl BlockPart for SignalSource {
    fn has_analog_output(&self, _: &dyn LevelHost, event: &mut HasAnalogOutputEvent) {
        event.output = true;
    }

    fn analog_output(&self, _: &dyn LevelHost, event: &mut AnalogOutputEvent) {
        event.output = 15;
    }
}

#[mod_api::horizon_mod]
impl Hooks for StoneSignal {
    fn register(&self, registrar: &mut dyn Registrar, _: &RegistrationContext) {
        let stone = registrar.block_key("minecraft:stone");
        registrar.block_part(stone, SignalSource);
    }

    fn player_logged_in(&self, host: &mut dyn ServerHost, event: &mut PlayerLoggedInEvent<'_>) {
        // Handles are resolved through the side-typed Host, never retained game references.
        if let Some(player) = host.player(event.player) {
            let _ = player.tell(host, Text::translate("example_mod.ready", Vec::new()));
        }
    }
}

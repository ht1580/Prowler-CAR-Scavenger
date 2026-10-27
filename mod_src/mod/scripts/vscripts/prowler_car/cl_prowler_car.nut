// Prowler.CAR.Scavenger - client-only cosmetics for the Prowler CAR viewmodel.
// The coil drum turns inside the model's own fire animation (like a bolt), so no script drives it.
// This only adds a short electric crackle on the coils while firing. Touches only the local
// first-person CAR model; no gameplay values.
global function ProwlerCAR_Init

const asset PROWLER_CAR_MODEL = $"models/weapons/car101/ptpov_car101.mdl"
const string PROWLER_COIL_ATTACH = "FX_spinner_coils"
const asset PROWLER_COIL_FX = $"P_spectre_dmg_elec"

const float FX_INTERVAL = 0.45

void function ProwlerCAR_Init()
{
	PrecacheParticleSystem( PROWLER_COIL_FX )
	thread ProwlerCAR_Think()
}

void function ProwlerCAR_Think()
{
	float nextFx = 0.0
	int lastClip = -1
	entity lastWeapon = null

	while ( true )
	{
		WaitFrame()

		entity player = GetLocalViewPlayer()
		if ( !IsValid( player ) )
			continue

		entity weapon = player.GetActiveWeapon()
		entity vm = player.GetViewModelEntity()
		if ( !IsValid( weapon ) || !IsValid( vm ) || weapon.GetWeaponClassName() != "mp_weapon_car" )
		{
			lastWeapon = null
			continue
		}
		// only our own model has the coil attachment (another CAR model mod would not)
		if ( vm.GetModelName() != PROWLER_CAR_MODEL || vm.LookupAttachment( PROWLER_COIL_ATTACH ) <= 0 )
			continue

		int clip = weapon.GetWeaponPrimaryClipCount()
		if ( weapon != lastWeapon )
		{
			lastWeapon = weapon
			lastClip = clip
		}

		int fired = lastClip - clip
		lastClip = clip
		float now = Time()
		if ( fired > 0 && fired < 10 && GetConVarBool( "prowler_car_fx" ) && now >= nextFx )
		{
			int attach = vm.LookupAttachment( PROWLER_COIL_ATTACH )
			StartParticleEffectOnEntity( vm, GetParticleSystemIndex( PROWLER_COIL_FX ), FX_PATTACH_POINT_FOLLOW, attach )
			nextFx = now + FX_INTERVAL
		}
	}
}

// Prowler.CAR.Scavenger - client-only cosmetics for the Prowler CAR viewmodel.
// Turns the reactive coil drum one chamber (1/3 turn) for every shot through the model's looping pose
// parameter "prowler_spin" (an autoplay delta layer on the stock bolt bone, which carries the drum), easing
// toward the target so a burst spins smoothly and the drum always stops on a chamber. No effects.
// Touches only the local first-person CAR model; no gameplay values.
global function ProwlerCAR_Init

const asset PROWLER_CAR_MODEL = $"models/weapons/car101/ptpov_car101.mdl"
const string PROWLER_SPIN_POSE = "prowler_spin"
const string PROWLER_DRUM_ATTACH = "FX_spinner_coils"   // marks our model (other CAR model mods lack it)

const float SPIN_PER_SHOT = 0.33333333   // turns: one of the drum's three chambers
const float SPIN_FOLLOW = 22.0           // 1/s: how fast the drum catches up with the shots fired

void function ProwlerCAR_Init()
{
	thread ProwlerCAR_Think()
}

void function ProwlerCAR_Think()
{
	float phase = 0.0
	float target = 0.0
	float lastTime = Time()
	int lastClip = -1
	entity lastWeapon = null

	while ( true )
	{
		WaitFrame()
		float now = Time()
		float dt = now - lastTime
		lastTime = now

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
		// only drive our own model (another CAR model mod has no such pose parameter / attachment)
		if ( vm.GetModelName() != PROWLER_CAR_MODEL || vm.LookupAttachment( PROWLER_DRUM_ATTACH ) <= 0 )
			continue

		int clip = weapon.GetWeaponPrimaryClipCount()
		if ( weapon != lastWeapon )
		{
			lastWeapon = weapon
			lastClip = clip
		}

		int fired = lastClip - clip
		lastClip = clip
		if ( fired > 0 && fired < 10 && GetConVarBool( "prowler_car_spin" ) )
			target += SPIN_PER_SHOT * fired

		phase += ( target - phase ) * min( 1.0, SPIN_FOLLOW * dt )
		if ( target - phase < 0.0005 )
			phase = target
		float whole = floor( phase )
		phase -= whole
		target -= whole
		vm.SetPoseParameter( PROWLER_SPIN_POSE, phase )
	}
}

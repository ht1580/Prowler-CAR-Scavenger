global function ProwlerStance_Init

struct
{
 bool running = false
} file

void function ProwlerStance_Init()
{
 if ( file.running )
  return
 file.running = true
 thread ProwlerStance_Think()
}

void function ProwlerStance_Think()
{
 entity previousWeapon = null
 int previousAmmo = -1
 float drumTarget = 0.0
 float drumPosition = 0.0
 float amount = 0.0
 for ( ;; )
 {
  WaitFrame()
  entity player = GetLocalViewPlayer()
  if ( !IsValid( player ) || player.IsTitan() )
   continue
  entity weapon = player.GetActiveWeapon()
  entity viewmodel = player.GetViewModelEntity()
  if ( !IsValid( weapon ) || !IsValid( viewmodel ) )
   continue
  if ( weapon.GetWeaponClassName() != "mp_weapon_car" )
  {
   previousWeapon = null
   amount = 0.0
   continue
  }
  int ammo = weapon.GetWeaponPrimaryClipCount()
  if ( weapon != previousWeapon )
  {
   previousAmmo = ammo
   previousWeapon = weapon
   amount = 0.0
  }
  if ( ammo < previousAmmo )
   drumTarget += float( previousAmmo - ammo )
  previousAmmo = ammo
  // Six physical chambers: one ammo decrement advances one sector, then stops.
  // Reload increases ammo and never advances or rewinds the drum.
  drumPosition = min( drumTarget, drumPosition + FrameTime() * 24.0 )
  float phase = ( drumPosition - floor( drumPosition / 6.0 ) * 6.0 ) / 6.0
  viewmodel.SetPoseParameter( "prowler_drum", phase )
  float target = 0.0
  if ( player.IsCrouched() && !weapon.IsReloading() && player.GetVelocity().LengthSqr() < 30000 )
   target = 1.0
  amount += ( target - amount ) * min( 1.0, FrameTime() * 12.0 )
  if ( amount < 0.001 )
   amount = 0.0
  if ( amount > 0.999 )
   amount = 1.0
  viewmodel.SetPoseParameter( "prowler_crouch", amount )
 }
}

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
  // Cosmetic state is separate from the MDL skin-family table. Keep both
  // local render entities on the authored Scavenger surface, without changing
  // the saved loadout or the pilot's arms/other weapons.
  if ( weapon.GetCamo() != 0 )
   weapon.SetCamo( 0 )
  if ( weapon.GetSkin() != 0 )
   weapon.SetSkin( 0 )
  if ( viewmodel.GetCamo() != 0 )
   viewmodel.SetCamo( 0 )
  if ( viewmodel.GetSkin() != 0 )
   viewmodel.SetSkin( 0 )
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
  // Airborne duck does not immediately change the grounded crouch hull.
  // Read the actual duck command too; vertical jump speed must not cancel it.
  if ( ( player.IsCrouched() || player.IsInputCommandHeld( IN_DUCK ) ) && !weapon.IsReloading() )
   target = 1.0
  amount += ( target - amount ) * min( 1.0, FrameTime() * 12.0 )
  if ( amount < 0.001 )
   amount = 0.0
  if ( amount > 0.999 )
   amount = 1.0
  viewmodel.SetPoseParameter( "prowler_crouch", amount )
 }
}

/*****************************************************************************/
#ifndef AXI_MOTOR_H
#define AXI_MOTOR_H
/*****************************************************************************/


/* Address Block: */
#define INTR_BASE_ADDR 0x0 /* Base address offset */

 /* Registers */
#define DGIER_ADDR_OFFSET 0x1C /* Address block offset */
#define IPISR_ADDR_OFFSET 0x20 /* Address block offset */


/* Address Block: */
#define SET_BASE_ADDR 0x80 /* Base address offset */

 /* Registers */
#define DECELERATION_ADDR_OFFSET 0x28 /* Address block offset */
#define ERR_LIM_LOW_ADDR_OFFSET 0x0 /* Address block offset */
#define ERR_LIM_HIGH_ADDR_OFFSET 0x4 /* Address block offset */
#define P_COEF_ADDR_OFFSET 0xC /* Address block offset */
#define I_MAX_ADDR_OFFSET 0x8 /* Address block offset */
#define D_COEF_ADDR_OFFSET 0x14 /* Address block offset */
#define I_COEF_ADDR_OFFSET 0x10 /* Address block offset */
#define COMMAND_ADDR_OFFSET 0x18 /* Address block offset */
#define LOAD_ADDR_OFFSET 0x1C /* Address block offset */
#define TARGET_VELOCITY_ADDR_OFFSET 0x20 /* Address block offset */
#define ACCELERATION_ADDR_OFFSET 0x24 /* Address block offset */
#define START_VELOCITY_ADDR_OFFSET 0x2C /* Address block offset */
#define QUAD_POSITION_ADDR_OFFSET 0x40 /* Address block offset */
#define CURRENT_POSITION_ADDR_OFFSET 0x3C /* Address block offset */
#define JERK_ADDR_OFFSET 0x38 /* Address block offset */
#define START_POSITION_ADDR_OFFSET 0x34 /* Address block offset */
#define TARGET_POSITION_ADDR_OFFSET 0x30 /* Address block offset */
#define DUTY_CYCLE_ADDR_OFFSET 0x44 /* Address block offset */
#define SOFT_RESET_ADDR_OFFSET 0x48 /* Address block offset */


/* Address Block: */
#define STS_BASE_ADDR 0x100 /* Base address offset */

 /* Registers */
#define TRAJ_BUSY_ADDR_OFFSET 0x0 /* Address block offset */
#define QUAD_POSITION_ADDR_OFFSET 0x38 /* Address block offset */
#define TRAJ_DECELERATION_DISTANCE_ADDR_OFFSET 0x14 /* Address block offset */
#define TRAJ_VELOCITY_ADDR_OFFSET 0x10 /* Address block offset */
#define TRAJ_DISTANCE_LEFT_ADDR_OFFSET 0xC /* Address block offset */
#define TRAJ_POSITION_ADDR_OFFSET 0x8 /* Address block offset */
#define TRAJ_STATUS_ADDR_OFFSET 0x4 /* Address block offset */
#define TRAJ_ERR_ADDR_OFFSET 0x18 /* Address block offset */
#define TRAJ_PID_ADDR_OFFSET 0x1C /* Address block offset */
#define TRAJ_ERR_SAT_ADDR_OFFSET 0x20 /* Address block offset */
#define TRAJ_PID_P_ADDR_OFFSET 0x24 /* Address block offset */
#define TRAJ_PID_I_ADDR_OFFSET 0x28 /* Address block offset */
#define TRAJ_PID_D_ADDR_OFFSET 0x2C /* Address block offset */
#define TRAJ_SIGN_ADDR_OFFSET 0x30 /* Address block offset */
#define TRAJ_DUTY_CYCLE_ADDR_OFFSET 0x34 /* Address block offset */

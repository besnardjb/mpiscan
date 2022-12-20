#include <mpi.h>
#include <stdio.h>


#define PRINT_VALUE_SIZE( CONSTANT ) do{ \
unsigned int size = sizeof(CONSTANT);\
char value[64];\
snprintf(value, 64, "%ld", (long int)CONSTANT);\
printf("\"value_%s\" : %s,\n", #CONSTANT, value);\
printf("\"size_%s\" : %d,\n", #CONSTANT, size); }while(0)





int main(int argc, char** argv)
{
	MPI_Init(&argc, &argv);

   printf("{\n");


   PRINT_VALUE_SIZE(MPI_BOTTOM);
   PRINT_VALUE_SIZE(MPI_IN_PLACE);

   printf("\"_\" : null}\n");

	MPI_Finalize();
	return 0;
}

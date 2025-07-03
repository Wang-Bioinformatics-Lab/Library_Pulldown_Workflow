run:
	nextflow run ./nf_workflow.nf -resume -c nextflow.config

run_no_cache:
	nextflow run ./nf_workflow.nf -c nextflow.config

run_slurm:
	nextflow run ./nf_workflow.nf -resume -c nextflow_slurm.config

init_modules:
	git submodule update --init --recursive